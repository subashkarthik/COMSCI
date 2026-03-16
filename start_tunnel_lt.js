const localtunnel = require('localtunnel');

(async () => {
  console.log("Starting Localtunnel...");
  try {
    const tunnel = await localtunnel({ port: 8000 });

    console.log("====================================================");
    console.log("  IMPORTANT: Copy the URL below:");
    console.log("  " + tunnel.url);
    console.log("  ");
    console.log("  1. Paste it into Meta Developer Portal.");
    console.log("  2. Add /webhook to the end.");
    console.log("  3. If you see a 'Reminder' page in browser,");
    console.log("     click 'Click to Continue' to allow traffic.");
    console.log("====================================================");

    tunnel.on('close', () => {
      console.log("Tunnel closed");
    });
  } catch (err) {
    console.error("Error starting localtunnel:", err);
  }
})();
