/**
 * AI Job Hunter Content Script (Agentic Auto-Detection & HITL Auto-Fill).
 * Runs inside browser session. Automatically observes DOM for LinkedIn Easy Apply,
 * Greenhouse, Lever, and Workday forms, auto-fills candidate facts, and highlights fields in yellow.
 * NEVER clicks submit (Strict Human-in-the-Loop safety).
 */

// Candidate Facts Store (Default + Dynamic Sync from Backend)
let CANDIDATE_PROFILE_FACTS = {
  first_name: "Mohammad Samir",
  last_name: "Khan",
  full_name: "Mohammad Samir Khan",
  email: "samirkhan003786@gmail.com",
  phone: "9876543210",
  city: "Mumbai, Maharashtra, India",
  linkedin: "https://linkedin.com/in/mohammad-samir-khan",
  github: "https://github.com/msamir-17",
  headline: "AI Engineer & Fullstack Developer",
  skills: "Python, AI/ML, FastAPI, React, TypeScript, PostgreSQL"
};

// Sync profile facts from backend if available
async function syncCandidateProfileFromBackend() {
  try {
    const response = await fetch("http://localhost:8000/api/v1/candidate-profile/active");
    if (response.ok) {
      const data = await response.json();
      if (data) {
        if (data.full_name) {
          CANDIDATE_PROFILE_FACTS.full_name = data.full_name;
          const parts = data.full_name.trim().split(" ");
          CANDIDATE_PROFILE_FACTS.first_name = parts[0] || CANDIDATE_PROFILE_FACTS.first_name;
          CANDIDATE_PROFILE_FACTS.last_name = parts.slice(1).join(" ") || CANDIDATE_PROFILE_FACTS.last_name;
        }
        if (data.email) CANDIDATE_PROFILE_FACTS.email = data.email;
        if (data.phone) CANDIDATE_PROFILE_FACTS.phone = data.phone;
        if (data.location) CANDIDATE_PROFILE_FACTS.city = data.location;
        if (data.headline) CANDIDATE_PROFILE_FACTS.headline = data.headline;
      }
    }
  } catch (e) {
    // Local fallback
  }
}
syncCandidateProfileFromBackend();


// Display non-intrusive Toast Notification on page
function showToastNotification(message) {
  let toast = document.getElementById("ai-job-hunter-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "ai-job-hunter-toast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      background: #0f172a;
      color: #38bdf8;
      border: 2px solid #0284c7;
      border-radius: 8px;
      padding: 12px 18px;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      transition: opacity 0.3s ease;
    `;
    document.body.appendChild(toast);
  }
  toast.innerHTML = `🎯 <strong>AI Job Hunter Sidecar:</strong> ${message}`;
  toast.style.opacity = "1";

  setTimeout(() => {
    if (toast) toast.style.opacity = "0";
  }, 4000);
}

function getFieldDescriptor(input) {
  let descriptor = "";
  descriptor += " " + (input.getAttribute('aria-label') || '');
  descriptor += " " + (input.placeholder || '');
  descriptor += " " + (input.name || '');
  descriptor += " " + (input.id || '');

  if (input.id) {
    try {
      const label = document.querySelector(`label[for="${CSS.escape(input.id)}"]`);
      if (label) descriptor += " " + label.innerText;
    } catch (e) {}
  }

  const parentContainer = input.closest('div, label, section, .fb-dash-form-element, .jobs-easy-apply-form-section__grouping');
  if (parentContainer) {
    descriptor += " " + parentContainer.innerText;
  }

  return descriptor.toLowerCase();
}

function setReactInputValue(input, value) {
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
  if (nativeInputValueSetter) {
    nativeInputValueSetter.call(input, value);
  } else {
    input.value = value;
  }
  
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
  input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
}

let lastFilledCount = 0;
let autofillDebounceTimer = null;

function autoFillFormFields(showToast = true) {
  const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select'));
  let fieldsFilled = 0;

  inputs.forEach(input => {
    if (['submit', 'button', 'checkbox', 'radio'].includes(input.type)) return;

    const descriptor = getFieldDescriptor(input);
    let valueToFill = null;

    if (descriptor.includes('mobile') || descriptor.includes('phone') || descriptor.includes('contact')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.phone;
    } else if (descriptor.includes('city') || descriptor.includes('location')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.city;
    } else if (descriptor.includes('first name') || descriptor.includes('firstname')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.first_name;
    } else if (descriptor.includes('last name') || descriptor.includes('lastname')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.last_name;
    } else if (descriptor.includes('email')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.email;
    } else if (descriptor.includes('linkedin')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.linkedin;
    } else if (descriptor.includes('github')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.github;
    }

    if (valueToFill && (!input.value || input.value.trim() === '')) {
      setReactInputValue(input, valueToFill);
      input.style.backgroundColor = '#fef08a'; // Light yellow highlight for human review
      input.style.border = '2px solid #eab308';
      input.dataset.aiAutofilled = "true";
      fieldsFilled++;
    }
  });

  if (fieldsFilled > 0 && showToast && fieldsFilled !== lastFilledCount) {
    lastFilledCount = fieldsFilled;
    showToastNotification(`Auto-filled ${fieldsFilled} fields. Please review before submitting.`);
  }

  return fieldsFilled;
}

// Automatic DOM Observer for Agentic Modal & Application Detection
const observer = new MutationObserver((mutations) => {
  clearTimeout(autofillDebounceTimer);
  autofillDebounceTimer = setTimeout(() => {
    // Check if job application modal or form is present on page
    const hasApplicationForm = document.querySelector('.jobs-easy-apply-modal, .artdeco-modal, form, [data-automation-id="jobApplicationForm"]');
    if (hasApplicationForm) {
      autoFillFormFields(true);
    }
  }, 400);
});

// Start observing document body for dynamic modal popups
observer.observe(document.body, { childList: true, subtree: true });

// Initial execution on page load
setTimeout(() => {
  autoFillFormFields(false);
}, 1000);

// Listen for popup trigger
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "TRIGGER_AUTOFILL") {
    const filled = autoFillFormFields(true);
    sendResponse({ status: "SUCCESS", fieldsFilled: filled });
  }
});
