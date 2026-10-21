// ========================================
// CODEVIEW COMMUNITY JAVASCRIPT
// ========================================


// ========================================
// SHOW AND HIDE COMMENTS
// ========================================

// Find every Comment button.
document.querySelectorAll(".comment-toggle").forEach((button) => {

    // Listen for clicks on this button.
    button.addEventListener("click", () => {

        // Find the comments section belonging to this post.
        const comments = document.getElementById(
            button.dataset.commentId
        );

        // Stop if the comments section cannot be found.
        if (!comments) {
            return;
        }

        // Show hidden comments or hide visible comments.
        comments.hidden = !comments.hidden;

        // Update the button's accessibility state.
        button.setAttribute(
            "aria-expanded",
            String(!comments.hidden)
        );

    });

});


// ========================================
// OPEN COMMENTS AFTER SUBMITTING
// ========================================

// Read the post ID from the page URL.
const searchParams = new URLSearchParams(window.location.search);
const openCommentsForPost = searchParams.get("comments");

// Open the comments section after a successful comment submission.
if (openCommentsForPost) {

    // Find the comments section.
    const comments = document.getElementById(
        `comments-${openCommentsForPost}`
    );

    // Find the corresponding Comment button.
    const button = document.querySelector(
        `.comment-toggle[data-comment-id="comments-${openCommentsForPost}"]`
    );

    if (comments && button) {

        // Display the comments.
        comments.hidden = false;

        // Mark the button as expanded.
        button.setAttribute("aria-expanded", "true");

    }

}


// ========================================
// SHARE COMMUNITY POSTS
// ========================================

// Find every Share button.
document.querySelectorAll(".share-button").forEach((button) => {

    // Listen for clicks on this button.
    button.addEventListener("click", async () => {

        // Build the full URL for the selected post.
        const url = new URL(
            button.dataset.shareUrl,
            window.location.origin
        ).href;

        try {

            // Use the device's share menu if supported.
            if (navigator.share) {

                await navigator.share({
                    title: "CodeView Post",
                    url: url
                });

            } else {

                // Copy the link when native sharing is unavailable.
                await navigator.clipboard.writeText(url);

                alert("Post link copied!");

            }

        } catch (error) {

            // Do nothing if the developer cancels sharing.
            if (error.name !== "AbortError") {

                // Offer a manual copy option if sharing fails.
                window.prompt(
                    "Copy this post link:",
                    url
                );

            }

        }

    });

});