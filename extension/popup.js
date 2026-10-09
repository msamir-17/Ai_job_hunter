document.getElementById('autofill-btn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const btn = document.getElementById('autofill-btn');
  btn.innerText = "Processing Autofill...";

  chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, (response) => {
    if (chrome.runtime.lastError) {
      btn.innerText = "Refresh Job Page First";
      setTimeout(() => { btn.innerText = "Auto-Fill Application Form"; }, 2500);
    } else if (response && response.status === "SUCCESS") {
      btn.innerText = `Auto-filled Form!`;
      setTimeout(() => { btn.innerText = "Auto-Fill Application Form"; }, 2500);
    }
  });
});
