// ============================================================
// CODEVIEW DEVELOPMENT ROOM — GITHUB FILE EXPLORER
// ============================================================

document.addEventListener("DOMContentLoaded", async () => {

    // Find the file explorer on the page.
    const fileTree = document.getElementById("github-file-tree");

    // Stop if the current page has no file explorer.
    if (!fileTree) {
        return;
    }

    // Get the Django endpoint that returns repository files.
    const filesUrl = fileTree.dataset.filesUrl;

    // Find the editor's active filename label.
    const activeFileName = document.getElementById("active-file-name");

    // Create a nested folder structure from flat GitHub paths.
    function buildTree(files) {

        const root = {
            folders: {},
            files: [],
        };

        for (const file of files) {

            // Separate the file path into folder/file names.
            const parts = file.path.split("/");

            let current = root;

            for (let index = 0; index < parts.length; index++) {

                const part = parts[index];
                const isLast = index === parts.length - 1;

                // Add folders to the tree.
                if (!isLast || file.type === "folder") {

                    if (!current.folders[part]) {
                        current.folders[part] = {
                            folders: {},
                            files: [],
                        };
                    }

                    current = current.folders[part];

                } else {

                    // Add a file to its containing folder.
                    current.files.push(file);
                }
            }
        }

        return root;
    }

    // Convert a folder structure into visible HTML elements.
    function renderTree(node, container) {

        // Sort folder names alphabetically.
        const folderNames = Object.keys(node.folders).sort();

        for (const folderName of folderNames) {

            // A details element creates an expandable folder.
            const folder = document.createElement("details");

            const summary = document.createElement("summary");
            summary.className = "explorer-item";

            // textContent prevents filenames from becoming HTML.
            summary.textContent = `📁 ${folderName}`;

            folder.appendChild(summary);

            const children = document.createElement("div");
            children.className = "explorer-children";

            // Display files and folders inside this folder.
            renderTree(node.folders[folderName], children);

            folder.appendChild(children);
            container.appendChild(folder);
        }

        // Sort files alphabetically.
        const sortedFiles = [...node.files].sort(
            (a, b) => a.name.localeCompare(b.name)
        );

        for (const file of sortedFiles) {

            const button = document.createElement("button");

            button.type = "button";
            button.className = "explorer-item";
            button.textContent = `📄 ${file.name}`;

            // For now, selecting a file displays its name.
            // Open the selected GitHub file in the editor.
            button.addEventListener("click", async () => {

                const editorContent = document.getElementById(
                    "editor-content"
                );

                const sourceCode = document.getElementById(
                    "source-code"
                );

                const sourceCodeText = document.getElementById(
                    "source-code-text"
                );

                const placeholder = document.getElementById(
                    "editor-placeholder"
                );

                // Show the selected filename.
                if (activeFileName) {
                    activeFileName.textContent = file.path;
                }

                // Check that all editor elements exist.
                if (
                    !editorContent ||
                    !sourceCode ||
                    !sourceCodeText ||
                    !placeholder
                ) {
                    return;
                }

                // Show a loading message.
                placeholder.textContent = "Loading source code...";
                placeholder.hidden = false;
                sourceCode.hidden = true;

                // Build the Django endpoint URL safely.
                const url = new URL(
                    editorContent.dataset.fileUrl,
                    window.location.origin
                );

                url.searchParams.set("path", file.path);

                try {

                    // Request the selected file from Django.
                    const response = await fetch(url, {
                        credentials: "same-origin",
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(
                            data.error || "Unable to open this file."
                        );
                    }

                    // textContent displays code safely as plain text.
                    sourceCodeText.textContent = data.content;

                    // Hide the placeholder and show the code.
                    placeholder.hidden = true;
                    sourceCode.hidden = false;

                } catch (error) {

                    placeholder.textContent = error.message;
                    placeholder.hidden = false;
                    sourceCode.hidden = true;
                }
            });

            container.appendChild(button);
        }
    }

    // Retrieve repository files from our Django backend.
    try {

        const response = await fetch(filesUrl, {
            credentials: "same-origin",
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to load repository files."
            );
        }

        // Convert GitHub's flat list into a folder tree.
        const tree = buildTree(data.files);

        // Remove the loading message.
        fileTree.replaceChildren();

        // Display the repository folders and files.
        renderTree(tree, fileTree);

        if (data.files.length === 0) {
            fileTree.textContent = "This repository has no files.";
        }

    } catch (error) {

        // Show a useful message if the request fails.
        fileTree.textContent = error.message;
    }
});