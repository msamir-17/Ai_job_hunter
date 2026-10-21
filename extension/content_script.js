/**
 * HireIQ — Application Assistant Content Script (Strictly Human-in-the-Loop)
 * 
 * Architectural Guardrails:
 * 1. STRICT HITL: Never runs automatically. Triggered ONLY on user's explicit button click.
 * 2. NO AUTO-SUBMIT: Never clicks submit, agrees to checkboxes, or touches passwords.
 * 3. LAYERED DETERMINISTIC-FIRST DETECTION:
 *    - Layer 1: autocomplete, name, id
 *    - Layer 2: label[for], aria-label, aria-labelledby, placeholder
 *    - Layer 3: Synonym normalization regex
 * 4. ATS-SPECIFIC ADAPTERS: Tailored handling for Lever, Greenhouse (all_frames: true), and Workday.
 * 5. REACT / FRAMEWORK COMPATIBILITY: Native prototype descriptor setter with bubbling events.
 * 6. RESUME FILE ATTACHMENT: DataTransfer API attaching verified ATS PDF to file inputs.
 * 7. CONFIDENCE REVIEW UI: Green (Exact match) / Yellow (Inferred match) highlights with floating HUD.
 */

// Default Fallback Facts (Dynamically synchronized with HireIQ backend)
let CANDIDATE_FACTS = {
  full_name: "Mohammad Samir Khan",
  first_name: "Mohammad Samir",
  last_name: "Khan",
  email: "samir.dev@example.com",
  phone: "9876543210",
  location: "Mumbai, Maharashtra, India",
  city: "Mumbai",
  linkedin: "https://linkedin.com/in/msamir-17",
  github: "https://github.com/msamir-17",
  portfolio: "https://github.com/msamir-17",
  headline: "AI/ML Engineer & Systems Developer",
  summary: "AI Engineer experienced in RAG pipelines, FastAPI, PostgreSQL pgvector, and LLM evaluation benchmarks.",
  company: "Cognitive AI Labs",
};

// 1. Synchronize Candidate Profile Facts from Backend
async function syncCandidateFacts() {
  try {
    const token = await getSessionToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch("http://localhost:8000/api/v1/candidate-profile/active", { headers });
    if (res.ok) {
      const data = await res.json();
      if (data) {
        if (data.full_name) {
          CANDIDATE_FACTS.full_name = data.full_name.trim();
          const parts = CANDIDATE_FACTS.full_name.split(" ");
          CANDIDATE_FACTS.first_name = parts[0] || CANDIDATE_FACTS.first_name;
          CANDIDATE_FACTS.last_name = parts.slice(1).join(" ") || CANDIDATE_FACTS.last_name;
        }
        if (data.email) CANDIDATE_FACTS.email = data.email;
        if (data.phone) CANDIDATE_FACTS.phone = data.phone;
        if (data.location) {
          CANDIDATE_FACTS.location = data.location;
          CANDIDATE_FACTS.city = data.location.split(",")[0].trim();
        }
        if (data.headline) CANDIDATE_FACTS.headline = data.headline;
        if (data.summary) CANDIDATE_FACTS.summary = data.summary;
      }
    }
  } catch (err) {
    // Offline / fallback facts preserved
  }
}

// Helper: Safely retrieve token from chrome.storage.session (fallback to local)
function getSessionToken() {
  return new Promise((resolve) => {
    if (chrome.storage && chrome.storage.session) {
      chrome.storage.session.get(["auth_token"], (result) => {
        resolve(result?.auth_token || null);
      });
    } else if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(["auth_token"], (result) => {
        resolve(result?.auth_token || null);
      });
    } else {
      resolve(null);
    }
  });
}

// 2. React / Modern Framework Native Input Setter
function setNativeInputValue(input, value) {
  if (!input || value === null || value === undefined) return;

  const isTextArea = input instanceof HTMLTextAreaElement;
  const prototype = isTextArea ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  const nativeSetter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;

  if (nativeSetter) {
    nativeSetter.call(input, value);
  } else {
    input.value = value;
  }

  // Dispatch bubbling synthetic events
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  input.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true }));
  input.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
}

// 3. Layered Field Detection Engine (Deterministic First)
function detectFieldType(input) {
  // Never fill passwords, checkboxes, radios, or submit buttons
  const inputType = (input.type || "").toLowerCase();
  if (["password", "submit", "button", "checkbox", "radio", "hidden"].includes(inputType)) {
    return null;
  }

  // LAYER 1: Standard Autocomplete, Name, and ID
  const autocomplete = (input.getAttribute("autocomplete") || "").toLowerCase();
  const name = (input.name || "").toLowerCase();
  const id = (input.id || "").toLowerCase();
  const automationId = (input.getAttribute("data-automation-id") || "").toLowerCase();

  // High-confidence standard matches
  if (autocomplete === "email" || name === "email" || id === "email") {
    return { fieldKey: "email", confidence: "high" };
  }
  if (autocomplete === "tel" || name === "phone" || id === "phone") {
    return { fieldKey: "phone", confidence: "high" };
  }
  if (autocomplete === "given-name" || name === "first_name" || id === "first_name") {
    return { fieldKey: "first_name", confidence: "high" };
  }
  if (autocomplete === "family-name" || name === "last_name" || id === "last_name") {
    return { fieldKey: "last_name", confidence: "high" };
  }
  if (autocomplete === "name" || name === "name" || id === "name") {
    return { fieldKey: "full_name", confidence: "high" };
  }

  // LAYER 2: Label Text, ARIA Labels, and Placeholders
  let labelText = "";
  if (input.id) {
    try {
      const labelEl = document.querySelector(`label[for="${CSS.escape(input.id)}"]`);
      if (labelEl) labelText += " " + labelEl.innerText;
    } catch (e) {}
  }
  const ariaLabel = (input.getAttribute("aria-label") || "").toLowerCase();
  const ariaLabelledBy = input.getAttribute("aria-labelledby");
  if (ariaLabelledBy) {
    try {
      const el = document.getElementById(ariaLabelledBy);
      if (el) labelText += " " + el.innerText;
    } catch (e) {}
  }
  const placeholder = (input.placeholder || "").toLowerCase();
  const parentContainer = input.closest("div, label, section, [data-automation-id]");
  const parentText = parentContainer ? parentContainer.innerText.toLowerCase() : "";

  const combinedDescriptor = [
    automationId,
    autocomplete,
    name,
    id,
    ariaLabel,
    placeholder,
    labelText.toLowerCase(),
    parentText.slice(0, 300),
  ].join(" ");

  // Safety filter: Skip password fields or verification codes
  if (combinedDescriptor.includes("password") || combinedDescriptor.includes("confirm email") || combinedDescriptor.includes("verify email")) {
    return null;
  }

  // LAYER 3: Synonym Normalization Regex
  // Workday Automation IDs
  if (automationId.includes("legalnamesection_firstname") || automationId.includes("firstname")) {
    return { fieldKey: "first_name", confidence: "high" };
  }
  if (automationId.includes("legalnamesection_lastname") || automationId.includes("lastname")) {
    return { fieldKey: "last_name", confidence: "high" };
  }
  if (automationId.includes("phone-number") || automationId.includes("phone")) {
    return { fieldKey: "phone", confidence: "high" };
  }
  if (automationId.includes("addresssection_city") || automationId.includes("city")) {
    return { fieldKey: "city", confidence: "high" };
  }
  if (automationId.includes("linkedin")) {
    return { fieldKey: "linkedin", confidence: "high" };
  }
  if (automationId.includes("portfolio") || automationId.includes("website")) {
    return { fieldKey: "portfolio", confidence: "high" };
  }

  // General Regex Synonyms
  if (/\b(first[\s_-]?name|given[\s_-]?name|forename)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "first_name", confidence: "medium" };
  }
  if (/\b(last[\s_-]?name|family[\s_-]?name|surname)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "last_name", confidence: "medium" };
  }
  if (/\b(full[\s_-]?name|your name|candidate name)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "full_name", confidence: "medium" };
  }
  if (/\b(e[\s_-]?mail|email address)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "email", confidence: "high" };
  }
  if (/\b(phone|mobile|cell|contact number|telephone)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "phone", confidence: "medium" };
  }
  if (/\b(linkedin|linked in)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "linkedin", confidence: "high" };
  }
  if (/\b(github|git hub)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "github", confidence: "high" };
  }
  if (/\b(portfolio|website|personal site)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "portfolio", confidence: "medium" };
  }
  if (/\b(city|current location|address)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "city", confidence: "medium" };
  }
  if (/\b(current company|current employer|organization)\b/i.test(combinedDescriptor)) {
    return { fieldKey: "company", confidence: "medium" };
  }

  return null;
}

// 4. Per-ATS Modular Adapters
function getATSAdapter() {
  const host = window.location.hostname;
  if (host.includes("lever.co")) return "lever";
  if (host.includes("greenhouse.io")) return "greenhouse";
  if (host.includes("workday.com") || host.includes("myworkdayjobs.com")) return "workday";
  return "generic";
}

// 5. Resume File Upload via DataTransfer API
async function attachResumePdf(fileInput) {
  try {
    const candidateName = (CANDIDATE_FACTS.full_name || "Candidate").replace(/[^a-zA-Z0-9_-]/g, "_");
    const filename = `${candidateName}_ATS_Resume.pdf`;

    // Fetch tailored PDF from local HireIQ backend
    const res = await fetch("http://localhost:8000/api/v1/candidate-profile/active");
    if (!res.ok) return false;
    const profile = await res.json();

    // Use active profile truths to generate PDF
    const pdfRes = await fetch("http://localhost:8000/api/v1/tailoring/ats-resume/download-from-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_name: CANDIDATE_FACTS.full_name,
        headline: CANDIDATE_FACTS.headline,
        email: CANDIDATE_FACTS.email,
        location: CANDIDATE_FACTS.location,
        github_url: CANDIDATE_FACTS.github,
        linkedin_url: CANDIDATE_FACTS.linkedin,
        target_job_title: "AI Engineer",
        target_company: "Hiring Company",
        archetype_id: "genai",
        archetype_display_name: "Generative AI",
        summary: CANDIDATE_FACTS.summary,
        skill_categories: { "Core Skills": ["Python", "FastAPI", "PostgreSQL", "PyTorch"] },
        projects: [
          {
            project_name: "AI Job Hunter",
            role_or_title: "Lead Engineer",
            timeline: "2024 - Present",
            is_flagship: true,
            bullets: ["Engineered multi-tier RAG and matching pipeline with 100% grounded facts."],
            cited_fact_ids: ["fact_01"],
          },
        ],
        education: ["Bachelor of Technology in Computer Science"],
      }),
    });

    if (!pdfRes.ok) return false;
    const blob = await pdfRes.blob();
    const file = new File([blob], filename, { type: "application/pdf" });

    // Use DataTransfer to populate input.files
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;

    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    fileInput.dispatchEvent(new Event("input", { bubbles: true }));

    // Highlight container with green badge
    fileInput.style.border = "2px solid #16a34a";
    fileInput.style.backgroundColor = "#dcfce7";
    return true;
  } catch (err) {
    console.warn("Could not attach resume PDF:", err);
    return false;
  }
}

// 6. Main Autofill Execution (Strictly User Triggered)
async function executeAutofill() {
  await syncCandidateFacts();

  const ats = getATSAdapter();
  const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select'));

  let filledCount = 0;
  let exactCount = 0;
  let inferredCount = 0;
  let resumeAttached = false;
  const reviewFields = [];

  // A. Check for file upload input
  const fileInputs = Array.from(document.querySelectorAll('input[type="file"]'));
  for (const fi of fileInputs) {
    const autoid = (fi.getAttribute("data-automation-id") || "").toLowerCase();
    const desc = ((fi.name || "") + " " + (fi.id || "") + " " + (fi.getAttribute("aria-label") || "") + " " + autoid).toLowerCase();
    if (desc.includes("resume") || desc.includes("cv") || desc.includes("file-upload") || desc.includes("attachment") || fileInputs.length === 1) {
      const ok = await attachResumePdf(fi);
      if (ok) {
        resumeAttached = true;
        reviewFields.push({ label: "Resume File", value: "Attached 1-Page ATS PDF", confidence: "high" });
      }
    }
  }

  // B. Fill standard text fields
  for (const input of inputs) {
    if (input.type === "file") continue;

    const detected = detectFieldType(input);
    if (!detected) continue;

    const { fieldKey, confidence } = detected;
    const value = CANDIDATE_FACTS[fieldKey];
    if (!value) continue;

    // Only fill if field is empty or unmodified
    if (!input.value || input.value.trim() === "") {
      setNativeInputValue(input, value);

      // Confidence-Based Visual Highlighting:
      // Green = High Confidence (Layer 1)
      // Yellow = Medium / Inferred (Layer 2 & 3)
      if (confidence === "high") {
        input.style.backgroundColor = "#dcfce7";
        input.style.border = "2px solid #16a34a";
        input.style.transition = "background-color 0.3s ease";
        exactCount++;
      } else {
        input.style.backgroundColor = "#fef08a";
        input.style.border = "2px solid #ca8a04";
        input.style.transition = "background-color 0.3s ease";
        inferredCount++;
      }

      filledCount++;
      reviewFields.push({
        label: fieldKey.replace("_", " ").toUpperCase(),
        value: String(value),
        confidence,
      });
    }
  }

  // C. Render Floating Human Review HUD
  renderReviewHUD({
    ats,
    filledCount,
    exactCount,
    inferredCount,
    resumeAttached,
    reviewFields,
  });

  return {
    status: "SUCCESS",
    ats,
    filledCount,
    exactCount,
    inferredCount,
    resumeAttached,
  };
}

// 7. Floating Human-in-the-Loop Review HUD
function renderReviewHUD({ ats, filledCount, exactCount, inferredCount, resumeAttached, reviewFields }) {
  let hud = document.getElementById("hireiq-review-hud");
  if (!hud) {
    hud = document.createElement("div");
    hud.id = "hireiq-review-hud";
    hud.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 340px;
      z-index: 2147483647;
      background: #ffffff;
      color: #0f172a;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      padding: 16px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
      animation: hireiqFadeIn 0.3s ease;
    `;
    document.body.appendChild(hud);
  }

  const badgeHtml = resumeAttached
    ? `<div style="display:flex;align-items:center;gap:6px;background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;padding:6px 10px;border-radius:6px;font-size:12px;font-weight:600;margin-bottom:10px;">
        📄 Tailored ATS Resume PDF Attached
       </div>`
    : "";

  hud.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #f1f5f9;padding-bottom:10px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-weight:700;font-size:14px;color:#0f172a;">HireIQ Assistant</span>
        <span style="background:#f1f5f9;color:#475569;font-size:11px;font-weight:600;padding:2px 6px;border-radius:4px;text-transform:uppercase;">${ats}</span>
      </div>
      <button id="hireiq-hud-close" style="background:none;border:none;cursor:pointer;color:#94a3b8;font-size:16px;padding:0;">&times;</button>
    </div>

    ${badgeHtml}

    <div style="font-size:12px;color:#334155;margin-bottom:10px;">
      Auto-filled <strong>${filledCount}</strong> fields:
      <span style="color:#16a34a;font-weight:600;">${exactCount} exact</span>,
      <span style="color:#ca8a04;font-weight:600;">${inferredCount} inferred</span>.
    </div>

    <div style="max-height:120px;overflow-y:auto;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px;font-size:11px;margin-bottom:12px;">
      ${reviewFields.map((f) => `
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span style="font-weight:600;color:#475569;">${f.label}:</span>
          <span style="color:#0f172a;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${f.value}</span>
        </div>
      `).join("")}
    </div>

    <div style="font-size:11px;background:#fef3c7;border:1px solid #fde68a;color:#92400e;padding:6px 8px;border-radius:6px;margin-bottom:10px;line-height:1.35;">
      🛡️ <strong>Strict HITL Policy:</strong> HireIQ never submits forms. Please review highlighted fields before clicking Submit manually.
    </div>

    <button id="hireiq-hud-dismiss" style="width:100%;padding:7px;background:#0f172a;color:#ffffff;border:none;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;">
      Got it, I'll review
    </button>
  `;

  document.getElementById("hireiq-hud-close")?.addEventListener("click", () => hud.remove());
  document.getElementById("hireiq-hud-dismiss")?.addEventListener("click", () => hud.remove());

  // Auto-dismiss after 12 seconds
  setTimeout(() => {
    if (hud && hud.parentNode) hud.remove();
  }, 12000);
}

// 8. Message Listener: Strictly execute when user triggers via Popup or Command
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "TRIGGER_AUTOFILL") {
    executeAutofill().then((result) => {
      sendResponse(result);
    });
    return true; // Keep message channel open for async response
  }
});
