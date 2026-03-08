const ngrok = require('ngrok');

(async function() {
  console.log("Starting Ngrok tunnel...");
  try {
    const url = await ngrok.connect(8000);
    console.log("===================================================");
    console.log("  IMPORTANT: Copy the URL below:");
    console.log("  " + url);
    console.log("  ");
    console.log("  Paste it into the Meta Developer Portal");
    console.log("  and make sure to add /webhook to the end!");
    console.log("===================================================");
    
    // Keep process alive
    process.stdin.resume();
  } catch (err) {
    console.error("Error starting ngrok:", err);
  }
})();
