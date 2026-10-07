document.getElementById('autofill-btn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, (response) => {
    if (chrome.runtime.lastError) {
      alert("Please refresh the job application page to initialize autofill.");
    } else if (response && response.status === "SUCCESS") {
      alert(`Autofilled ${response.fieldsFilled} form fields! Please review before submitting.`);
    }
  });
});
