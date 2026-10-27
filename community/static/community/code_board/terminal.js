// ========================================
// CODEVIEW PRIVATE DEVELOPER TERMINAL
// ========================================

// Wait until the HTML page finishes loading.
document.addEventListener("DOMContentLoaded", function () {

    // Find the terminal HTML elements.
    const terminalContainer = document.getElementById("terminal-container");
    const terminalStatus = document.getElementById("terminal-status");

    // Stop if the required HTML elements are missing.
    if (!terminalContainer || !terminalStatus) {
        return;
    }

    // Check whether the xterm.js library loaded successfully.
    if (typeof Terminal === "undefined") {
        terminalStatus.textContent = "Terminal library unavailable";
        return;
    }

    // Create the browser terminal.
    const terminal = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: "monospace",

        theme: {
            background: "#0d1117",
            foreground: "#e5e7eb",
            cursor: "#ffffff",
        },
    });

    // Display the terminal inside the HTML container.
    terminal.open(terminalContainer);

    // Display the welcome message.
    terminal.writeln("Welcome to CodeView Terminal!");
    terminal.writeln("Connecting to your private terminal...");
    terminal.writeln("");

    // Get the development group ID from HTML.
    const groupId = terminalContainer.dataset.groupId;

    // Ensure the group ID is valid.
    if (!/^[1-9]\d*$/.test(groupId || "")) {
        terminalStatus.textContent = "Invalid group";
        terminal.writeln("Invalid development group.");
        return;
    }

    // Choose the correct WebSocket protocol.
    // HTTPS uses wss:// while HTTP uses ws://.
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    // Create the terminal WebSocket URL.
    const socketUrl = (
        `${protocol}://${window.location.host}/ws/groups/${groupId}/terminal/`
    );

    // Connect the browser terminal to Django Channels.
    const terminalSocket = new WebSocket(socketUrl);

    // ========================================
    // 1. WEBSOCKET CONNECTION OPENED
    // ========================================

    terminalSocket.addEventListener("open", function () {

        // Update the connection status.
        terminalStatus.textContent = "Connected";

    });

    // ========================================
    // 2. RECEIVE MESSAGES FROM DJANGO
    // ========================================

    terminalSocket.addEventListener("message", function (event) {

        let data;

        // Convert the received JSON string into a JavaScript object.
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            terminal.writeln("Invalid response from terminal server.");
            return;
        }

        // Display the successful connection message.
        if (data.type === "terminal_connected") {

            terminal.writeln(data.message);
            terminal.writeln("");
            terminal.writeln("Waiting for isolated terminal runner...");

        }

        // Display informational messages from Django.
        if (data.type === "terminal_info") {

            terminal.writeln(data.message);

        }

    });

    // ========================================
    // 3. WEBSOCKET CONNECTION CLOSED
    // ========================================

    terminalSocket.addEventListener("close", function (event) {

        // Update the connection status.
        terminalStatus.textContent = "Disconnected";

        // Explain why the connection closed.
        if (event.code === 4401) {

            terminal.writeln("Authentication required.");

        } else if (event.code === 4403) {

            terminal.writeln("You do not have access to this terminal.");

        } else {

            terminal.writeln("Terminal connection closed.");

        }

    });

    // ========================================
    // 4. WEBSOCKET CONNECTION ERROR
    // ========================================

    terminalSocket.addEventListener("error", function () {

        // Display the connection error.
        terminalStatus.textContent = "Connection error";

    });

    // ========================================
    // 5. CLOSE CONNECTION WHEN LEAVING
    // ========================================

    window.addEventListener("pagehide", function () {

        // Close the WebSocket when the developer leaves the page.
        terminalSocket.close();

    });

});