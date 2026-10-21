// HireIQ Assistant Popup Script
document.addEventListener("DOMContentLoaded", async () => {
  const profileNameEl = document.getElementById("profile-name");
  const profileEmailEl = document.getElementById("profile-email");
  const atsIndicatorEl = document.getElementById("ats-indicator");
  const autofillBtn = document.getElementById("autofill-btn");
  const resultBox = document.getElementById("result-box");

  // 1. Sync Profile Facts
  try {
    const res = await fetch("http://localhost:8000/api/v1/candidate-profile/active");
    if (res.ok) {
      const data = await res.json();
      profileNameEl.innerText = data.full_name || "Mohammad Samir Khan";
      profileEmailEl.innerText = data.email || "samir.dev@example.com";
    } else {
      profileNameEl.innerText = "Mohammad Samir Khan (Local)";
      profileEmailEl.innerText = "samir.dev@example.com";
    }
  } catch (err) {
    profileNameEl.innerText = "Mohammad Samir Khan (Local)";
    profileEmailEl.innerText = "samir.dev@example.com";
  }

  // 2. Identify Current Tab ATS Platform
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab?.url || "";

  if (url.includes("lever.co")) {
    atsIndicatorEl.innerText = "Target ATS: Lever Application";
  } else if (url.includes("greenhouse.io")) {
    atsIndicatorEl.innerText = "Target ATS: Greenhouse (Iframe-Aware)";
  } else if (url.includes("workday.com") || url.includes("myworkdayjobs.com")) {
    atsIndicatorEl.innerText = "Target ATS: Workday Wizard";
  } else {
    atsIndicatorEl.innerText = "Generic Application Form";
    atsIndicatorEl.style.color = "#475569";
    atsIndicatorEl.style.background = "#f1f5f9";
    atsIndicatorEl.style.borderColor = "#cbd5e1";
  }

  // 3. User Triggered Autofill Click
  autofillBtn.addEventListener("click", async () => {
    if (!tab?.id) return;

    autofillBtn.disabled = true;
    autofillBtn.innerText = "Auto-filling fields...";
    resultBox.style.display = "none";

    chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, (response) => {
      autofillBtn.disabled = false;
      autofillBtn.innerText = "Auto-Fill Application Form";

      if (chrome.runtime.lastError) {
        resultBox.className = "result-box result-warn";
        resultBox.innerText = "Could not reach tab. Please refresh the job page first.";
        resultBox.style.display = "block";
        return;
      }

      if (response && response.status === "SUCCESS") {
        resultBox.className = "result-box result-success";
        const fileMsg = response.resumeAttached ? " 📄 Resume PDF attached." : "";
        resultBox.innerHTML = `<strong>Done!</strong> Filled ${response.filledCount} fields (${response.exactCount} exact, ${response.inferredCount} inferred).${fileMsg}`;
        resultBox.style.display = "block";
      }
    });
  });

  // 4. Screening Questions Q&A Agent Integration
  const qaInput = document.getElementById("qa-question-input");
  const qaBtn = document.getElementById("qa-generate-btn");
  const qaResultBox = document.getElementById("qa-result-box");
  const qaAnswerText = document.getElementById("qa-answer-text");
  const qaMeta = document.getElementById("qa-meta");
  const qaCopyBtn = document.getElementById("qa-copy-btn");

  if (qaBtn && qaInput) {
    qaBtn.addEventListener("click", async () => {
      const q = qaInput.value.trim();
      if (!q) return;

      qaBtn.disabled = true;
      qaBtn.innerText = "Synthesizing Grounded Answer...";
      qaResultBox.style.display = "none";

      try {
        const token = await new Promise((resolve) => {
          if (chrome.storage?.session) {
            chrome.storage.session.get(["auth_token"], (r) => resolve(r?.auth_token || null));
          } else if (chrome.storage?.local) {
            chrome.storage.local.get(["auth_token"], (r) => resolve(r?.auth_token || null));
          } else {
            resolve(null);
          }
        });

        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch("http://localhost:8000/api/v1/screening-qa/answer", {
          method: "POST",
          headers,
          body: JSON.stringify({
            question: q,
            job_title: "Target Role",
          }),
        });

        if (res.ok) {
          const data = await res.json();
          qaAnswerText.innerText = data.answer;
          
          let metaStr = `Confidence: ${(data.confidence_score * 100).toFixed(0)}%`;
          if (data.cited_fact_ids && data.cited_fact_ids.length > 0) {
            metaStr += ` • Cited: ${data.cited_fact_ids.length} verified facts`;
          }
          if (data.missing_facts && data.missing_facts.length > 0) {
            metaStr += ` • Flagged missing: ${data.missing_facts.join(", ")}`;
          }
          qaMeta.innerText = metaStr;
          qaResultBox.style.display = "block";
        } else {
          qaAnswerText.innerText = "Error contacting HireIQ backend. Make sure the backend server is running.";
          qaMeta.innerText = "";
          qaResultBox.style.display = "block";
        }
      } catch (err) {
        qaAnswerText.innerText = "Could not reach HireIQ service: " + err.message;
        qaMeta.innerText = "";
        qaResultBox.style.display = "block";
      } finally {
        qaBtn.disabled = false;
        qaBtn.innerText = "Generate Grounded Answer";
      }
    });

    qaCopyBtn.addEventListener("click", () => {
      if (!qaAnswerText.innerText) return;
      navigator.clipboard.writeText(qaAnswerText.innerText).then(() => {
        qaCopyBtn.innerText = "✅ Copied!";
        setTimeout(() => {
          qaCopyBtn.innerText = "📋 Copy Answer";
        }, 2000);
      });
    });
  }
});
