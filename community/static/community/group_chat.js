/* ==========================================
   CODEVIEW — GROUP CHAT
   File: group_chat.js

   Features:
   1. File attachments
   2. Message replies
   3. Message validation
   4. Automatic scrolling
   5. Edit messages
   6. Cancel editing
   7. Delete messages
   8. Cancel deletion
========================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* ========================================
       1. GET CHAT ELEMENTS
    ======================================== */

    // Get the main chat form.
    const chatForm = document.getElementById("chat-form");

    // Get the attachment button.
    const attachButton = document.getElementById(
        "attach-file-button"
    );

    // Get the hidden file input.
    const fileInput = document.querySelector(
        "#group-chat input[type='file']"
    );

    // Get the hidden message type input.
    const messageType = document.querySelector(
        "#chat-form input[name='message_type']"
    );

    // Get the message textarea.
    const messageInput = document.getElementById(
        "id_content"
    );

    // Get the selected filename display.
    const fileNameDisplay = document.getElementById(
        "selected-file-name"
    );

    // Get the hidden reply ID input.
    const replyToInput = document.getElementById(
        "reply-to-id"
    );

    // Get the message history container.
    const chatMessages = document.getElementById(
        "chat-messages"
    );

    // Stop if the user cannot access Group Chat.
    if (!chatForm) {
        return;
    }


    /* ========================================
       2. FILE ATTACHMENTS
    ======================================== */

    if (attachButton && fileInput) {

        // Open the browser's file picker.
        attachButton.addEventListener("click", function () {

            fileInput.click();

        });

        // Detect when a file is selected.
        fileInput.addEventListener("change", function () {

            const selectedFile = fileInput.files[0];

            // Update the message type.
            if (messageType) {

                messageType.value = selectedFile
                    ? "file"
                    : "text";
            }

            // Display or hide the filename.
            if (fileNameDisplay) {

                fileNameDisplay.textContent = selectedFile
                    ? "📎 " + selectedFile.name
                    : "";

                fileNameDisplay.hidden = !selectedFile;
            }

        });

    }


    /* ========================================
       3. REPLY TO MESSAGES
    ======================================== */

    const replyButtons = document.querySelectorAll(
        ".reply-button"
    );

    replyButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Get the original message information.
            const messageId = button.dataset.messageId;
            const sender = button.dataset.sender;

            // Store the message being replied to.
            if (replyToInput) {
                replyToInput.value = messageId;
            }

            // Update the textarea placeholder.
            if (messageInput) {

                messageInput.placeholder =
                    "Replying to " + sender + "...";

                messageInput.focus();
            }

        });

    });


    /* ========================================
       4. SEND MESSAGE VALIDATION
    ======================================== */

    chatForm.addEventListener("submit", function (event) {

        // Get the message text.
        const message = messageInput
            ? messageInput.value.trim()
            : "";

        // Check for an attachment.
        const hasFile = Boolean(
            fileInput && fileInput.files.length > 0
        );

        // Prevent sending empty messages.
        if (!message && !hasFile) {

            event.preventDefault();

            alert(
                "Please enter a message or attach a file."
            );

            return;
        }

        // Set the correct message type.
        if (messageType) {

            messageType.value = hasFile
                ? "file"
                : "text";
        }

    });


    /* ========================================
       5. AUTOMATIC MESSAGE SCROLLING
    ======================================== */

    if (chatMessages) {

        // Scroll to the latest message.
        chatMessages.scrollTop =
            chatMessages.scrollHeight;

    }


    /* ========================================
       6. EDIT CHAT MESSAGES
    ======================================== */

    const editButtons = document.querySelectorAll(
        ".edit-button"
    );

    editButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Get the selected message ID.
            const messageId = button.dataset.messageId;

            // Find its editing form.
            const editForm = document.getElementById(
                "edit-form-" + messageId
            );

            if (!editForm) {
                return;
            }

            // Close other edit forms.
            document.querySelectorAll(
                ".message-edit-form"
            ).forEach(function (form) {

                if (form !== editForm) {
                    form.reset();
                    form.hidden = true;
                }

            });

            // Close any open delete confirmation.
            document.querySelectorAll(
                ".message-delete-form"
            ).forEach(function (form) {

                form.hidden = true;

            });

            // Show the selected editing form.
            editForm.hidden = false;

            // Focus the edit textarea.
            const editInput = editForm.querySelector(
                ".message-edit-input"
            );

            if (editInput) {

                editInput.focus();

                // Move the cursor to the end.
                editInput.setSelectionRange(
                    editInput.value.length,
                    editInput.value.length
                );
            }

        });

    });


    /* ========================================
       7. CANCEL MESSAGE EDITING
    ======================================== */

    const editCancelButtons = document.querySelectorAll(
        ".edit-cancel-button"
    );

    editCancelButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Find the editing form.
            const editForm = button.closest(
                ".message-edit-form"
            );

            if (!editForm) {
                return;
            }

            // Restore the original message.
            editForm.reset();

            // Hide the editing form.
            editForm.hidden = true;

        });

    });


    /* ========================================
       8. VALIDATE EDITED MESSAGES
    ======================================== */

    const editForms = document.querySelectorAll(
        ".message-edit-form"
    );

    editForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            // Get the edit textarea.
            const editInput = form.querySelector(
                ".message-edit-input"
            );

            if (!editInput) {

                event.preventDefault();

                return;
            }

            // Remove unnecessary spaces.
            const updatedMessage = editInput.value.trim();

            // Prevent empty edited messages.
            if (!updatedMessage) {

                event.preventDefault();

                alert(
                    "Your message cannot be empty."
                );

                editInput.focus();

                return;
            }

            // Save the trimmed text.
            editInput.value = updatedMessage;

            // Allow Django to process the form.
        });

    });


    /* ========================================
       9. DELETE CHAT MESSAGES
    ======================================== */

    const deleteButtons = document.querySelectorAll(
        ".delete-button"
    );

    deleteButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Get the selected message ID.
            const messageId = button.dataset.messageId;

            // Find its deletion form.
            const deleteForm = document.getElementById(
                "delete-form-" + messageId
            );

            if (!deleteForm) {
                return;
            }

            // Close other delete confirmations.
            document.querySelectorAll(
                ".message-delete-form"
            ).forEach(function (form) {

                form.hidden = true;

            });

            // Close all editing forms.
            document.querySelectorAll(
                ".message-edit-form"
            ).forEach(function (form) {

                form.reset();
                form.hidden = true;

            });

            // Display the delete confirmation.
            deleteForm.hidden = false;

            // Focus the Cancel button for accessibility.
            const cancelButton = deleteForm.querySelector(
                ".delete-cancel-button"
            );

            if (cancelButton) {
                cancelButton.focus();
            }

        });

    });


    /* ========================================
       10. CANCEL MESSAGE DELETION
    ======================================== */

    const deleteCancelButtons = document.querySelectorAll(
        ".delete-cancel-button"
    );

    deleteCancelButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Find the deletion form.
            const deleteForm = button.closest(
                ".message-delete-form"
            );

            if (deleteForm) {

                // Hide without deleting the message.
                deleteForm.hidden = true;
            }

        });

    });

});