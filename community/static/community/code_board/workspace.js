/**
 * CodeView — Developer Workspace
 *
 * Manages files in the browser using IndexedDB.
 *
 * Developers can:
 * - Create files.
 * - Switch between files.
 * - Write code.
 * - Automatically save changes.
 * - Restore files after leaving the page.
 * - Delete files.
 *
 * Temporary source code is NOT saved to PostgreSQL.
 */

document.addEventListener("DOMContentLoaded", async () => {

    // ========================================================
    // 1. FIND HTML ELEMENTS
    // ========================================================

    const editor = document.getElementById("code-editor");

    const languageSelector = document.getElementById("code-language");

    const fileList = document.getElementById("workspace-file-list");

    const newFileButton = document.getElementById("new-file-btn");

    const filenameDisplay = document.querySelector(".editor-filename");

    const languageDisplay = document.querySelector(".editor-language");

    const workspaceStatus = document.getElementById("workspace-status");

    // The HTML will provide these trusted Django values.
    const workspaceElement = document.getElementById(
        "codeview-workspace"
    );

    // Stop if the workspace HTML is not ready.
    if (
        !editor ||
        !languageSelector ||
        !fileList ||
        !newFileButton ||
        !workspaceElement ||
        !window.CodeViewStorage
    ) {
        return;
    }

    // ========================================================
    // 2. IDENTIFY THE DEVELOPER'S WORKSPACE
    // ========================================================

    const groupId = workspaceElement.dataset.groupId;

    const developerId = workspaceElement.dataset.developerId;

    // Separate files by developer and group.
    const workspaceId = `developer-${developerId}-group-${groupId}`;

    // Currently selected file.
    let activeFile = null;

    // Timer used to avoid saving on every keystroke.
    let saveTimer = null;

    // Track the latest save operation.
    let saveQueue = Promise.resolve();

    // ========================================================
    // 3. HELPER FUNCTIONS
    // ========================================================

    function showStatus(message) {
        if (workspaceStatus) {
            workspaceStatus.textContent = message;
        }
    }

    function getLanguageFromFilename(filename) {

        const extension = filename.split(".").pop().toLowerCase();

        const languages = {
            py: "python",
            go: "go",
            js: "javascript",
        };

        return languages[extension] || "python";
    }

    function getDefaultFilename(language) {

        const filenames = {
            python: "main.py",
            go: "main.go",
            javascript: "main.js",
        };

        return filenames[language] || "main.py";
    }

    function makeFileId(filename) {
        return `${workspaceId}:${filename}`;
    }

    function updateEditorHeader(file) {

        if (filenameDisplay) {
            filenameDisplay.textContent = file.name;
        }

        if (languageDisplay) {
            languageDisplay.textContent = file.language;
        }
    }

    // ========================================================
    // 4. SAVE THE CURRENT FILE
    // ========================================================

    async function saveActiveFile() {

        if (!activeFile) {
            return;
        }

        // Capture the current editor contents.
        const fileToSave = {
            ...activeFile,
            code: editor.value,
            language: languageSelector.value,
            updatedAt: new Date().toISOString(),
        };

        // Update the current in-memory file immediately.
        activeFile = fileToSave;

        // Serialize writes so older saves cannot overwrite newer ones.
        const write = saveQueue
            .catch(() => {})
            .then(() => window.CodeViewStorage.saveFile(fileToSave));

        saveQueue = write;

        try {
            await write;
            showStatus("Saved in this browser");
        } catch (error) {
            showStatus("Unable to save changes");
            console.error("CodeView save error:", error);
        }
    }

    function scheduleSave() {

        // Cancel the previous timer.
        clearTimeout(saveTimer);

        showStatus("Unsaved changes...");

        // Save after the developer stops typing briefly.
        saveTimer = setTimeout(() => {
            saveActiveFile();
        }, 400);
    }

    async function flushPendingSave() {

        clearTimeout(saveTimer);

        await saveActiveFile();
    }

    // ========================================================
    // 5. DISPLAY THE FILE LIST
    // ========================================================

    async function renderFileList() {

        const files = await window.CodeViewStorage.getFiles(
            workspaceId
        );

        // Sort filenames alphabetically.
        files.sort((a, b) => a.name.localeCompare(b.name));

        fileList.replaceChildren();

        for (const file of files) {

            const row = document.createElement("div");
            row.className = "workspace-file";

            if (activeFile && file.id === activeFile.id) {
                row.classList.add("active");
            }

            // Button for opening a file.
            const openButton = document.createElement("button");

            openButton.type = "button";
            openButton.className = "workspace-open-file";
            openButton.textContent = file.name;

            openButton.addEventListener("click", async () => {
                await openFile(file.id);
            });

            // Button for deleting a file.
            const deleteButton = document.createElement("button");

            deleteButton.type = "button";
            deleteButton.className = "workspace-delete-file";
            deleteButton.textContent = "×";
            deleteButton.title = `Delete ${file.name}`;

            deleteButton.addEventListener("click", async () => {
                await removeFile(file.id);
            });

            row.appendChild(openButton);
            row.appendChild(deleteButton);

            fileList.appendChild(row);
        }
    }

    // ========================================================
    // 6. OPEN A FILE
    // ========================================================

    async function openFile(fileId) {

        // Save the current file before switching.
        if (activeFile) {
            await flushPendingSave();
        }

        const file = await window.CodeViewStorage.getFile(fileId);

        if (!file) {
            showStatus("File not found");
            return;
        }

        activeFile = file;

        editor.value = file.code || "";

        languageSelector.value = file.language;

        updateEditorHeader(file);

        await renderFileList();

        showStatus("File opened");
    }

    // ========================================================
    // 7. CREATE A FILE
    // ========================================================

    async function createFile() {

        // Save the current file before creating another.
        if (activeFile) {
            await flushPendingSave();
        }

        const filename = window.prompt(
            "Enter a filename, for example: utils.py"
        );

        if (filename === null) {
            return;
        }

        const name = filename.trim();

        // Keep filenames simple and safe.
        if (
            !name ||
            name.length > 100 ||
            !/^[a-zA-Z0-9_.-]+$/.test(name) ||
            name === "." ||
            name === ".."
        ) {
            window.alert("Enter a valid filename.");
            return;
        }

        const fileId = makeFileId(name);

        // Prevent overwriting an existing file.
        const existingFile = await window.CodeViewStorage.getFile(
            fileId
        );

        if (existingFile) {
            window.alert("A file with this name already exists.");
            return;
        }

        const language = getLanguageFromFilename(name);

        const file = {
            id: fileId,
            workspaceId: workspaceId,
            name: name,
            language: language,
            code: "",
            updatedAt: new Date().toISOString(),
        };

        await window.CodeViewStorage.saveFile(file);

        await openFile(file.id);
    }

    // ========================================================
    // 8. DELETE A FILE
    // ========================================================

    async function removeFile(fileId) {

        const file = await window.CodeViewStorage.getFile(fileId);

        if (!file) {
            return;
        }

        const confirmed = window.confirm(
            `Delete ${file.name}? This cannot be undone.`
        );

        if (!confirmed) {
            return;
        }

        // Save pending edits before deleting a different file.
        clearTimeout(saveTimer);

        if (activeFile && activeFile.id !== fileId) {
            await saveActiveFile();
        }

        await saveQueue.catch(() => {});

        await window.CodeViewStorage.deleteFile(fileId);

        if (activeFile && activeFile.id === fileId) {
            activeFile = null;
            editor.value = "";
        }

        const remainingFiles = await window.CodeViewStorage.getFiles(
            workspaceId
        );

        if (remainingFiles.length > 0) {
            await openFile(remainingFiles[0].id);
        } else {
            await createDefaultFile();
        }

        await renderFileList();
    }

    // ========================================================
    // 9. CREATE THE DEFAULT FILE
    // ========================================================

    async function createDefaultFile() {

        const language = "python";

        const name = getDefaultFilename(language);

        const file = {
            id: makeFileId(name),
            workspaceId: workspaceId,
            name: name,
            language: language,
            code: "",
            updatedAt: new Date().toISOString(),
        };

        await window.CodeViewStorage.saveFile(file);

        await openFile(file.id);
    }

    // ========================================================
    // 10. RESTORE FILES WHEN THE PAGE OPENS
    // ========================================================

    async function initializeWorkspace() {

        try {

            const files = await window.CodeViewStorage.getFiles(
                workspaceId
            );

            if (files.length === 0) {

                // First visit: create an empty Python file.
                await createDefaultFile();

            } else {

                // Restore the most recently edited file.
                files.sort((a, b) => {
                    return b.updatedAt.localeCompare(a.updatedAt);
                });

                await openFile(files[0].id);
            }

            showStatus("Workspace ready");

        } catch (error) {

            showStatus("Browser storage unavailable");

            console.error("CodeView workspace error:", error);
        }
    }

    // ========================================================
    // 11. CONNECT EDITOR EVENTS
    // ========================================================

    // Automatically save while typing.
    editor.addEventListener("input", scheduleSave);

    // Save when changing the programming language.
    languageSelector.addEventListener("change", () => {

        updateEditorHeader({
            name: activeFile?.name || "",
            language: languageSelector.value,
        });

        scheduleSave();
    });

    // Create a new file.
    newFileButton.addEventListener("click", createFile);

    // Save immediately when leaving the editor.
    editor.addEventListener("blur", () => {
        if (activeFile) {
            clearTimeout(saveTimer);
            saveActiveFile();
        }
    });

    // Try to save when the page becomes hidden.
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden" && activeFile) {
            clearTimeout(saveTimer);
            saveActiveFile();
        }
    });

    // ========================================================
    // 12. START THE WORKSPACE
    // ========================================================

    await initializeWorkspace();

});