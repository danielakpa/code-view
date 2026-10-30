/**
 * CodeView — Code Board Execution
 *
 * Sends code directly from the browser to Django.
 * Source code is not saved to PostgreSQL.
 */

document.addEventListener("DOMContentLoaded", () => {

    // ========================================================
    // 1. FIND HTML ELEMENTS
    // ========================================================

    const editor = document.getElementById("code-editor");

    const languageSelector = document.getElementById("code-language");

    const runButton = document.getElementById("run-code-btn");

    const output = document.getElementById("execution-output");

    const status = document.getElementById("execution-status");

    // The HTML will provide this URL using Django's URL system.
    const runUrl = runButton?.dataset.runUrl;

    // Stop if this page does not contain the execution interface.
    if (
        !editor ||
        !languageSelector ||
        !runButton ||
        !output ||
        !status ||
        !runUrl
    ) {
        return;
    }

    // ========================================================
    // 2. READ DJANGO'S CSRF TOKEN
    // ========================================================

    const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    )?.value;

    // ========================================================
    // 3. RUN CODE FUNCTION
    // ========================================================

    async function runCode() {

        // Read the current code without saving it.
        const source = editor.value;

        // Read the selected programming language.
        const language = languageSelector.value;

        // Reject empty code before contacting Django.
        if (!source.trim()) {
            status.textContent = "Invalid code";
            output.textContent = "Write some code before running it.";
            return;
        }

        // Prevent multiple clicks while execution is pending.
        runButton.disabled = true;

        status.textContent = "Running...";

        output.textContent = "Executing your code...";

        try {

            // Create a form-style POST request.
            const formData = new FormData();

            formData.append("language", language);

            formData.append("code", source);

            // Send the code to Django.
            const response = await fetch(runUrl, {
                method: "POST",

                headers: {
                    "X-CSRFToken": csrfToken,
                },

                body: formData,

                credentials: "same-origin",
            });

            // Read Django's JSON response.
            const result = await response.json();

            // Display errors returned by Django.
            if (!response.ok) {
                status.textContent = "Execution failed";

                output.textContent =
                    result.error || "Unable to execute code.";

                return;
            }

            // =================================================
            // 4. DISPLAY EXECUTION RESULTS
            // =================================================

            const stdout = result.stdout || "";

            const stderr = result.stderr || "";

            // Read the exit code returned by the FastAPI execution pipeline.
            // 0 means the program completed successfully.
            const exitCode = result.return_code;

            // Combine normal output and error output.
            const messages = [];

            if (stdout) {
                messages.push(stdout);
            }

            if (stderr) {
                messages.push(stderr);
            }

            // Display a message if the program prints nothing.
            if (messages.length === 0) {
                messages.push("Program finished without output.");
            }

            // Show the execution output.
            output.textContent = messages.join("\n");

// Check whether execution exceeded the allowed time.
if (result.timed_out === true) {

    status.textContent = "Timed out";

    // Explain the timeout when no error output was returned.
    if (!stderr) {
        output.textContent += "\nExecution exceeded the time limit.";
    }

} else if (exitCode === 0) {

    // The program executed successfully.
    status.textContent = "Completed";

} else {

    // The program ran but returned a nonzero exit code.
    status.textContent = "Execution failed";
}

        } catch (error) {

            // Handle network errors or invalid responses.
            status.textContent = "Connection error";

            output.textContent =
                "Unable to contact the execution service.";

            console.error("CodeView execution error:", error);

        } finally {

            // Allow the developer to run code again.
            runButton.disabled = false;
        }
    }

    // ========================================================
    // 5. CONNECT THE RUN BUTTON
    // ========================================================

    runButton.addEventListener("click", runCode);

});