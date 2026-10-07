/**
 * AI Job Hunter Content Script.
 * Runs in user's browser session on job application portals.
 * Safe HITL auto-fill: fills form inputs, highlights fields for review, NEVER clicks submit.
 */

// Candidate Facts Store (Local session cache)
const CANDIDATE_PROFILE_FACTS = {
  first_name: "Aarav",
  last_name: "Sharma",
  full_name: "Aarav Sharma",
  email: "aarav.sharma@example.com",
  phone: "+91 9876543210",
  linkedin: "https://linkedin.com/in/aarav-sharma",
  github: "https://github.com/aarav-sharma",
  headline: "Software Engineer II - Python & AI/ML",
  skills: "Python, PyTorch, FastAPI, PostgreSQL, LangChain, Docker"
};

function autoFillFormFields() {
  const inputs = document.querySelectorAll('input, textarea');
  let fieldsFilled = 0;

  inputs.forEach(input => {
    const name = (input.name || input.id || input.placeholder || input.getAttribute('aria-label') || '').toLowerCase();
    let valueToFill = null;

    if (name.includes('first_name') || name.includes('firstname')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.first_name;
    } else if (name.includes('last_name') || name.includes('lastname')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.last_name;
    } else if (name.includes('name') && !name.includes('company')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.full_name;
    } else if (name.includes('email')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.email;
    } else if (name.includes('phone') || name.includes('mobile')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.phone;
    } else if (name.includes('linkedin')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.linkedin;
    } else if (name.includes('github')) {
      valueToFill = CANDIDATE_PROFILE_FACTS.github;
    }

    if (valueToFill && !input.value) {
      input.value = valueToFill;
      input.style.backgroundColor = '#fef08a'; // Light yellow highlight for human review
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      fieldsFilled++;
    }
  });

  return fieldsFilled;
}

// Listen for popup trigger
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "TRIGGER_AUTOFILL") {
    const filled = autoFillFormFields();
    sendResponse({ status: "SUCCESS", fieldsFilled: filled });
  }
});
