// ========================================
// CODEVIEW PRIVATE DEVELOPER TERMINAL
// ========================================

// Wait until the HTML page has finished loading.
document.addEventListener("DOMContentLoaded", function () {

    // Find the terminal container in our HTML.
    const terminalContainer = document.getElementById("terminal-container");

    // Find the terminal connection status.
    const terminalStatus = document.getElementById("terminal-status");

    // Stop if the terminal container does not exist.
    if (!terminalContainer) {
        return;
    }

    // Check whether the xterm.js library loaded successfully.
    if (typeof Terminal === "undefined") {

        terminalStatus.textContent = "Terminal library unavailable";

        return;
    }

    // Create a new terminal instance.
    const terminal = new Terminal({

        // Position of the cursor.
        cursorBlink: true,

        // Text size.
        fontSize: 14,

        // Terminal font.
        fontFamily: "monospace",

        // Terminal appearance.
        theme: {
            background: "#0d1117",
            foreground: "#e5e7eb",
            cursor: "#ffffff",
        },

    });

    // Display the terminal inside our HTML container.
    terminal.open(terminalContainer);

    // Show a welcome message.
    terminal.writeln("Welcome to CodeView Terminal!");
    terminal.writeln("Your private development workspace.");
    terminal.writeln("");

    // Explain that the terminal backend is not connected yet.
    terminal.writeln("Waiting for secure terminal connection...");

    // Update the connection status.
    terminalStatus.textContent = "Not connected";

});