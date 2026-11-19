"use strict";

const byId = (id) => document.getElementById(id);
const terminalStatuses = new Set(["completed", "needs_review", "failed", "unsupported", "cancelled"]);
const recentStorageKey = "invoice-extract-recent-jobs-v1";
const state = { file: null, job: null, jobId: null, fileName: null, pollTimer: null, activeTab: "overview", previewUrl: null, previewFileId: null, toastTimer: null };

function node(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined && value !== null) element.textContent = String(value);
  return element;
}

function clear(element) { element.replaceChildren(); return element; }
function human(value) { return String(value || "—").replaceAll("_", " "); }
function shown(value) { return value === null || value === undefined || value === "" ? "—" : String(value); }
function localTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "medium" });
}
function shortId(value) { return value ? `${value.slice(0, 8)}…${value.slice(-4)}` : "—"; }
function plural(count, noun) { return `${count} ${noun}${count === 1 ? "" : "s"}`; }

function toast(message) {
  const target = byId("toast");
  target.textContent = message;
  target.classList.remove("hidden");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => target.classList.add("hidden"), 3000);
}

function banner(message, kind = "error") {
  const target = byId("message-banner");
  if (!message) { target.classList.add("hidden"); return; }
  target.textContent = message;
  target.className = `message-banner${kind === "info" ? " info" : ""}`;
}

async function responseData(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : { detail: await response.text() };
  if (!response.ok) {
    const detail = data.detail;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail || data);
    throw new Error(message || `HTTP ${response.status}`);
  }
  return data;
}

function readRecent() {
  try {
    const data = JSON.parse(localStorage.getItem(recentStorageKey) || "[]");
    return Array.isArray(data) ? data.filter((entry) => entry && typeof entry.jobId === "string").slice(0, 8) : [];
  } catch { return []; }
}

function saveRecent(jobId, fileName) {
  try {
    const entries = readRecent().filter((entry) => entry.jobId !== jobId);
    entries.unshift({ jobId, fileName: fileName || `Job ${shortId(jobId)}`, at: new Date().toISOString() });
    localStorage.setItem(recentStorageKey, JSON.stringify(entries.slice(0, 8)));
  } catch { /* Browser storage may be unavailable. */ }
  renderRecent();
}

function renderRecent() {
  const target = clear(byId("recent-list"));
  const entries = readRecent();
  if (!entries.length) { target.append(node("p", "quiet", "No recent jobs yet.")); return; }
  for (const entry of entries) {
    const button = node("button", `recent-item${entry.jobId === state.jobId ? " active" : ""}`);
    button.type = "button";
    button.title = entry.jobId;
    button.append(node("span", "recent-icon", "DOC"));
    const text = node("span", "recent-text");
    text.append(node("strong", "", entry.fileName), node("small", "", shortId(entry.jobId)));
    button.append(text);
    button.addEventListener("click", () => openJob(entry.jobId, entry.fileName));
    target.append(button);
  }
}

function setFile(file) {
  if (!file) return;
  const allowed = ["pdf", "docx", "png", "jpg", "jpeg"];
  const extension = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(extension)) { state.file = null; byId("selected-file").classList.add("hidden"); byId("upload-button").disabled = true; banner("Choose a PDF, DOCX, PNG or JPEG file."); return; }
  if (file.size > 25 * 1024 * 1024) { state.file = null; byId("selected-file").classList.add("hidden"); byId("upload-button").disabled = true; banner("This file is larger than the 25 MB upload limit."); return; }
  state.file = file;
  byId("selected-file").textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
  byId("selected-file").classList.remove("hidden");
  byId("upload-button").disabled = false;
  banner(null);
}

async function uploadSelected() {
  if (!state.file) return;
  const button = byId("upload-button");
  button.disabled = true;
  button.textContent = "Uploading…";
  banner(null);
  try {
    const form = new FormData();
    form.append("file", state.file);
    const uploaded = await responseData(await fetch("/v1/files/upload", { method: "POST", body: form }));
    if (!uploaded.extraction_job_id) throw new Error("Upload succeeded, but no extraction job ID was returned. Use the file ID to submit a job through the API.");
    const fileName = state.file.name;
    saveRecent(uploaded.extraction_job_id, fileName);
    toast("Upload complete. Extraction is running.");
    await openJob(uploaded.extraction_job_id, fileName);
  } catch (error) {
    banner(`Could not upload: ${error.message}`);
  } finally {
    button.disabled = !state.file;
    button.textContent = "Upload and extract";
  }
}

function stopPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = null;
}

function releasePreview() {
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.previewUrl = null;
  state.previewFileId = null;
}

async function openJob(jobId, fileName) {
  const cleanId = String(jobId || "").trim();
  if (!cleanId) return;
  stopPolling();
  releasePreview();
  state.job = null;
  state.jobId = cleanId;
  history.replaceState(null, "", `/app?job=${encodeURIComponent(cleanId)}`);
  state.fileName = fileName || `Job ${shortId(cleanId)}`;
  state.activeTab = "overview";
  byId("job-id-input").value = cleanId;
  byId("empty-state").classList.add("hidden");
  byId("job-view").classList.remove("hidden");
  byId("job-title").textContent = state.fileName;
  byId("job-subtitle").textContent = "Loading the extraction result…";
  byId("job-id-display").textContent = cleanId;
  byId("job-status").textContent = "Loading";
  byId("job-status").className = "status-badge processing";
  clear(byId("job-metrics"));
  for (const panel of ["overview", "source", "timeline", "json"]) clear(byId(`panel-${panel}`));
  selectTab("overview");
  renderRecent();
  banner(null);
  await fetchJob(cleanId);
  if (state.jobId === cleanId && state.job && !terminalStatuses.has(state.job.status)) {
    state.pollTimer = setInterval(() => fetchJob(cleanId), 2000);
  }
}

async function fetchJob(jobId) {
  try {
    const data = await responseData(await fetch(`/v1/extractions/${encodeURIComponent(jobId)}`, { cache: "no-store" }));
    if (state.jobId !== jobId) return;
    state.job = data;
    renderJob(data);
    saveRecent(jobId, state.fileName);
    if (terminalStatuses.has(data.status)) stopPolling();
    banner(null);
    if (state.fileName?.startsWith("Job ") && data.file_id) {
      try {
        const file = await responseData(await fetch(`/v1/files/${encodeURIComponent(data.file_id)}`));
        if (state.jobId === jobId && file.original_name) {
          state.fileName = file.original_name;
          byId("job-title").textContent = file.original_name;
          saveRecent(jobId, file.original_name);
        }
      } catch { /* The job is still usable without file metadata. */ }
    }
  } catch (error) {
    if (state.jobId !== jobId) return;
    banner(`Could not load this job: ${error.message}`);
    if (!state.job) stopPolling();
  }
}

function selectTab(name) {
  state.activeTab = name;
  for (const button of document.querySelectorAll(".tab")) {
    const active = button.dataset.tab === name;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  }
  for (const panel of ["overview", "source", "timeline", "json"]) {
    byId(`panel-${panel}`).classList.toggle("hidden", panel !== name);
  }
}

function metric(value, label) {
  const element = node("div", "metric");
  element.append(node("strong", "", value), node("span", "", label));
  return element;
}

function card(title, caption) {
  const section = node("section", "section-card");
  const head = node("div", "section-head");
  head.append(node("h3", "", title));
  if (caption) head.append(node("p", "", caption));
  section.append(head);
  return section;
}

function field(label, value, money = false) {
  const item = node("div", "field");
  const empty = value === null || value === undefined || value === "";
  item.append(node("span", "field-label", label), node("span", `field-value${empty ? " empty" : ""}${money ? " money" : ""}`, shown(value)));
  return item;
}

function renderJob(data) {
  const status = data.status || "queued";
  const document = data.result?.document || {};
  const pages = data.source_document?.pages || [];
  const issues = data.validation?.issues || [];
  byId("job-status").textContent = human(status);
  byId("job-status").className = `status-badge ${status}`;
  byId("job-title").textContent = state.fileName || `${human(document.document_type)} result`;
  const stageText = status === "processing" || status === "queued" ? `Current stage: ${human(data.stage)}` : `Document type: ${human(document.document_type || data.processing_steps?.find((step) => step.action === "document_classified" && step.status === "completed")?.details?.document_type)}`;
  byId("job-subtitle").textContent = stageText;
  byId("job-id-display").textContent = data.job_id;
  const metrics = clear(byId("job-metrics"));
  metrics.append(metric(pages.length, "Pages read"), metric(data.processing_steps?.length || 0, "Steps recorded"), metric(data.models_used?.length || 0, "AI roles used"), metric(issues.length, "Validation issues"));
  renderOverview(data);
  renderSource(data);
  renderTimeline(data);
  renderRaw(data);
}

function renderOverview(data) {
  const target = clear(byId("panel-overview"));
  const issues = data.validation?.issues || [];
  const document = data.result?.document || {};
  const totals = document.totals || {};
  const models = data.models_used || [];

  if (data.status === "unsupported") {
    const section = card("Text extracted; financial fields unavailable");
    section.append(node("p", "empty-copy", data.error?.message || "This document is outside the supported invoice, bill, and receipt types."));
    target.append(section);
  } else if (data.error || issues.length) {
    const section = card(data.status === "needs_review" ? "Needs a closer look" : "Processing notes", plural(issues.length, "issue"));
    const list = node("div", "issue-list");
    for (const issue of issues) {
      const item = node("div", `issue ${issue.severity || ""}`);
      item.append(node("strong", "", human(issue.code)), node("p", "", issue.message || "Review this field."));
      if (issue.field_path) item.append(node("small", "", issue.field_path));
      list.append(item);
    }
    if (data.error) {
      const item = node("div", "issue high");
      item.append(node("strong", "", human(data.error.code)), node("p", "", data.error.message || "The job could not complete."));
      list.append(item);
    }
    section.append(list);
    target.append(section);
  } else if (data.status === "completed") {
    const section = card("Validation passed");
    section.append(node("div", "success-note", "No validation issues were reported for this extraction."));
    target.append(section);
  } else {
    const section = card("Extraction in progress");
    section.append(node("p", "empty-copy", "The worker is reading your document. This view refreshes automatically until the job finishes."));
    target.append(section);
  }

  if (data.text_extraction) {
    const textCard = card("Extracted text", `${plural(data.text_extraction.pages?.length || 0, "page")} · ${human(data.text_extraction.status)}`);
    const textValue = data.text_extraction.text || "No readable text was found.";
    const copy = node("button", "secondary-button", "Copy text");
    copy.type = "button";
    copy.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(data.text_extraction.text || ""); toast("Extracted text copied."); }
      catch { toast("Clipboard is unavailable in this browser."); }
    });
    textCard.append(copy, node("pre", "plain-text", textValue));
    target.append(textCard);
  }

  const pages = data.source_document?.pages || [];
  const methods = [...new Set(pages.flatMap((page) => page.methods || []))];
  const ocrUsed = pages.some((page) => (page.text_blocks || []).some((block) => String(block.source || "").includes("ocr")) || (page.methods || []).some((method) => String(method).includes("ocr")));
  const selectedModels = data.processing_steps?.find((step) => step.action === "ai_models_selected")?.details || {};
  const readingCard = card("Reading & OCR", "Configured tools and methods actually used for this document");
  const readingGrid = node("div", "field-grid");
  readingGrid.append(field("Reader status", human(data.source_document?.reader_status)), field("Methods used", methods.length ? methods.map(human).join(", ") : "Not read yet"), field("OCR engine configured", selectedModels.ocr?.engine), field("OCR actually used", ocrUsed ? "Yes" : "No"), field("Vision AI actually used", models.some((model) => model.role === "vision") ? "Yes" : "No"), field("OCR cleanup actually used", models.some((model) => model.role === "ocr_cleanup") ? "Yes" : "No"));
  readingCard.append(readingGrid);
  target.append(readingCard);

  const modelsCard = card("AI models actually used", data.configured_extraction_model ? `Selected: ${data.configured_extraction_model}` : "");
  const modelList = node("div", "model-list");
  if (models.length) {
    for (const model of models) {
      const chip = node("div", "model-chip");
      chip.append(node("strong", "", human(model.role)), node("span", "", `${model.provider} · ${model.model}`));
      modelList.append(chip);
    }
  } else modelList.append(node("p", "empty-copy", "No AI model has completed a step for this job yet."));
  modelsCard.append(modelList);
  target.append(modelsCard);

  if (!data.result) return;
  const summary = card("Document details", "Fields extracted from source content");
  const summaryGrid = node("div", "field-grid");
  summaryGrid.append(field("Type", human(document.document_type)), field("Document number", document.document_number), field("Document date", document.document_date), field("Due date", document.due_date), field("Currency", document.currency), field("Language", document.language));
  summary.append(summaryGrid);
  target.append(summary);

  for (const [title, party] of [["Seller", document.seller], ["Buyer", document.buyer]]) {
    const partyCard = card(title);
    const partyGrid = node("div", "field-grid");
    partyGrid.append(field("Name", party?.name), field("GSTIN", party?.gstin), field("Tax ID", party?.tax_id), field("Address", party?.address), field("Contact", party?.contact));
    partyCard.append(partyGrid);
    target.append(partyCard);
  }

  const amounts = card("Amounts", "Review the validation notes above before relying on totals");
  const amountsGrid = node("div", "field-grid");
  for (const [label, value] of [["Grand total", totals.grand_total], ["Subtotal", totals.subtotal], ["Tax total", totals.tax_total], ["CGST", totals.cgst], ["SGST", totals.sgst], ["IGST", totals.igst], ["Cess", totals.cess], ["Discount", totals.discount_total], ["Shipping", totals.shipping], ["Other charges", totals.other_charges], ["Round off", totals.round_off]]) amountsGrid.append(field(label, value, true));
  amounts.append(amountsGrid);
  target.append(amounts);

  const paymentCard = card("Payment");
  const paymentGrid = node("div", "field-grid");
  paymentGrid.append(field("Status", human(document.payment?.payment_status)), field("Method", document.payment?.payment_method), field("Amount paid", document.payment?.amount_paid, true), field("Balance due", document.payment?.balance_due, true), field("Transaction reference", document.payment?.transaction_reference));
  paymentCard.append(paymentGrid);
  target.append(paymentCard);

  const items = document.line_items || [];
  const lineCard = card("Line items", plural(items.length, "item"));
  if (items.length) {
    const wrap = node("div", "table-wrap");
    const table = node("table", "data-table");
    const header = node("tr");
    for (const label of ["Description", "HSN / SAC", "Unit", "Qty", "Unit price", "Discount", "Tax rate", "Tax amount", "Amount"]) header.append(node("th", "", label));
    table.append(node("thead")); table.tHead.append(header);
    const body = node("tbody");
    for (const item of items) {
      const row = node("tr");
      row.append(node("td", "", shown(item.description)));
      for (const value of [item.hsn_sac, item.unit]) row.append(node("td", "", shown(value)));
      for (const value of [item.quantity, item.unit_price, item.discount, item.tax_rate, item.tax_amount, item.amount]) row.append(node("td", "numeric", shown(value)));
      body.append(row);
    }
    table.append(body); wrap.append(table); lineCard.append(wrap);
  } else lineCard.append(node("p", "empty-copy", "No line items were extracted."));
  target.append(lineCard);

  const citations = data.result.evidence || [];
  const evidenceCard = card("Source evidence", plural(citations.length, "citation"));
  const evidenceList = node("div", "evidence-list");
  for (const evidence of citations) {
    const item = node("div", "evidence-item");
    item.append(node("strong", "", shown(evidence.field_path)), node("p", "", shown(evidence.raw_text)), node("small", "", `Page ${evidence.page_number} · ${evidence.block_ids?.join(", ") || "No block"}`));
    evidenceList.append(item);
  }
  if (!citations.length) evidenceList.append(node("p", "empty-copy", "No source citations were returned."));
  evidenceCard.append(evidenceList);
  target.append(evidenceCard);
}

function sourceTable(tableData) {
  const section = node("div");
  section.append(node("h4", "source-subhead", `Table ${tableData.table_id}`));
  const wrap = node("div", "source-table-wrap");
  const table = node("table", "source-table");
  for (const rowData of tableData.rows || []) {
    const row = node("tr");
    for (const value of rowData) row.append(node("td", "", shown(value)));
    table.append(row);
  }
  wrap.append(table); section.append(wrap);
  return section;
}

function previewNode(sourceFormat) {
  const box = node("div", "preview-box");
  if (!state.previewUrl) {
    box.append(node("p", "preview-placeholder", "Load the original file to see it here. The extracted text and tables are listed below."));
    return box;
  }
  if (sourceFormat === "application/pdf") {
    const frame = node("iframe");
    frame.src = state.previewUrl;
    frame.title = "Original PDF preview";
    box.append(frame);
  } else if (sourceFormat?.startsWith("image/")) {
    const image = node("img");
    image.src = state.previewUrl;
    image.alt = "Original uploaded document";
    box.append(image);
  } else box.append(node("p", "preview-placeholder", "Browser preview is available for PDF and image files. Download this document to view the original."));
  return box;
}

async function loadPreview(fileId) {
  try {
    const response = await fetch(`/v1/files/${encodeURIComponent(fileId)}/download`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    if (state.job?.file_id !== fileId) return;
    releasePreview();
    state.previewUrl = URL.createObjectURL(blob);
    state.previewFileId = fileId;
    if (state.job?.file_id === fileId) renderSource(state.job);
  } catch (error) { banner(`Could not preview the original file: ${error.message}`); }
}

function renderSource(data) {
  const target = clear(byId("panel-source"));
  const source = data.source_document;
  if (!source) {
    const section = card("Source content");
    section.append(node("p", "empty-copy", "Source text is not available yet. It appears once the reader finishes."));
    target.append(section);
    return;
  }
  const intro = card("Original and extracted content", `${plural(source.pages?.length || 0, "page")} · ${human(source.reader_status)}`);
  intro.append(node("p", "section-caption", "This is what the reader observed. Native text, OCR text and AI candidates stay separate so you can compare them."));
  const actions = node("div", "source-actions");
  const download = node("a", "secondary-button", "Download original");
  download.href = `/v1/files/${encodeURIComponent(data.file_id)}/download`;
  actions.append(download);
  if (source.source_format === "application/pdf" || source.source_format?.startsWith("image/")) {
    const button = node("button", "secondary-button", state.previewFileId === data.file_id ? "Reload preview" : "Preview original");
    button.type = "button";
    button.addEventListener("click", () => loadPreview(data.file_id));
    actions.append(button);
  }
  intro.append(actions);
  if (source.source_format === "application/pdf" || source.source_format?.startsWith("image/")) intro.append(previewNode(source.source_format));
  target.append(intro);

  for (const page of source.pages || []) {
    const details = node("details", "page-card");
    if (page.page_number === 1) details.open = true;
    const summary = node("summary");
    summary.append(node("span", "", `Page ${page.page_number}`), node("span", "page-meta", `${(page.methods || []).join(" + ") || "no method"} · ${plural(page.text_blocks?.length || 0, "block")}`));
    details.append(summary);
    const body = node("div", "page-body");
    if (page.warnings?.length) for (const warning of page.warnings) body.append(node("p", "source-warning", `${warning.code}: ${warning.message}`));
    const blocks = node("div");
    blocks.append(node("h4", "source-subhead", "Text blocks"));
    const blockList = node("div", "source-block-list");
    for (const block of page.text_blocks || []) {
      const item = node("div", "source-block");
      const head = node("div", "source-block-head");
      head.append(node("span", "", block.block_id), node("span", "source-tag", human(block.source)));
      if (block.confidence !== null && block.confidence !== undefined) head.append(node("span", "", `${Math.round(block.confidence * 100)}% confidence`));
      item.append(head, node("p", "", block.text));
      blockList.append(item);
    }
    if (!page.text_blocks?.length) blockList.append(node("p", "empty-copy", "No text blocks on this page."));
    blocks.append(blockList); body.append(blocks);
    for (const table of page.tables || []) body.append(sourceTable(table));
    details.append(body); target.append(details);
  }
  if (source.warnings?.length) {
    const warnings = card("Reader warnings");
    for (const warning of source.warnings) warnings.append(node("p", "source-warning", `${warning.code}: ${warning.message}`));
    target.append(warnings);
  }
}

function renderTimeline(data) {
  const target = clear(byId("panel-timeline"));
  const steps = data.processing_steps || [];
  const section = card("Processing timeline", `${plural(steps.length, "recorded step")} · oldest first`);
  section.append(node("p", "section-caption", "Configured models are listed when the worker starts. A model was actually called only when its step appears as completed."));
  const list = node("div", "timeline-list");
  for (const step of steps) {
    const item = node("div", "timeline-item");
    item.append(node("span", `timeline-marker ${step.status}`, step.sequence));
    const content = node("div", "timeline-content");
    const top = node("div", "timeline-top");
    const time = node("time", "", localTime(step.at));
    if (step.at) time.dateTime = step.at;
    top.append(node("strong", "", human(step.action)), time);
    content.append(top);
    const meta = node("div", "timeline-meta");
    meta.append(node("span", "", human(step.phase)), node("span", "", human(step.status)));
    const details = step.details || {};
    if (details.provider && details.model) meta.append(node("span", "", `${details.provider} · ${details.model}`));
    if (details.decision) meta.append(node("span", "", human(details.decision)));
    content.append(meta);
    if (Object.keys(details).length) {
      const disclosure = node("details", "timeline-details");
      disclosure.append(node("summary", "", "View step details"), node("pre", "", JSON.stringify(details, null, 2)));
      content.append(disclosure);
    }
    item.append(content); list.append(item);
  }
  if (!steps.length) list.append(node("p", "empty-copy", "No processing steps have been recorded yet."));
  section.append(list); target.append(section);
}

function renderRaw(data) {
  const target = clear(byId("panel-json"));
  const section = node("section", "section-card");
  const head = node("div", "raw-head");
  head.append(node("h3", "", "Complete API response"));
  const button = node("button", "secondary-button", "Copy JSON");
  button.type = "button";
  button.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(JSON.stringify(state.job, null, 2)); toast("JSON copied to clipboard."); }
    catch { toast("Clipboard is unavailable in this browser."); }
  });
  head.append(button);
  section.append(head, node("pre", "code-view", JSON.stringify(data, null, 2)));
  target.append(section);
}

async function checkService() {
  const target = byId("service-state");
  try {
    const response = await fetch("/health/ready", { cache: "no-store" });
    target.className = `service-state ${response.ok ? "ready" : "down"}`;
    target.lastElementChild.textContent = response.ok ? "Service ready" : "Service unavailable";
  } catch {
    target.className = "service-state down";
    target.lastElementChild.textContent = "Service unavailable";
  }
}

byId("drop-zone").addEventListener("click", () => byId("file-input").click());
byId("file-input").addEventListener("change", (event) => setFile(event.target.files?.[0]));
for (const eventName of ["dragenter", "dragover"]) byId("drop-zone").addEventListener(eventName, (event) => { event.preventDefault(); byId("drop-zone").classList.add("dragover"); });
for (const eventName of ["dragleave", "drop"]) byId("drop-zone").addEventListener(eventName, (event) => { event.preventDefault(); byId("drop-zone").classList.remove("dragover"); });
byId("drop-zone").addEventListener("drop", (event) => setFile(event.dataTransfer?.files?.[0]));
byId("upload-button").addEventListener("click", uploadSelected);
byId("lookup-form").addEventListener("submit", (event) => { event.preventDefault(); openJob(byId("job-id-input").value.trim()); });
byId("clear-recent").addEventListener("click", () => { try { localStorage.removeItem(recentStorageKey); } catch { /* Storage may be disabled. */ } renderRecent(); toast("Recent jobs cleared from this browser."); });
byId("copy-job-id").addEventListener("click", async () => { try { await navigator.clipboard.writeText(state.jobId || ""); toast("Job ID copied."); } catch { toast("Clipboard is unavailable in this browser."); } });
for (const tab of document.querySelectorAll(".tab")) tab.addEventListener("click", () => selectTab(tab.dataset.tab));
byId("job-view").querySelector(".tab-bar").addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  const tabs = [...document.querySelectorAll(".tab")];
  const current = tabs.indexOf(document.activeElement);
  if (current < 0) return;
  event.preventDefault();
  const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
  selectTab(tabs[next].dataset.tab);
  tabs[next].focus();
});

renderRecent();
checkService();
const jobFromUrl = new URLSearchParams(location.search).get("job");
if (jobFromUrl) openJob(jobFromUrl);
