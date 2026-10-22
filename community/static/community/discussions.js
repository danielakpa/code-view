/**
 * CodeView Discussion Interactions
 *
 * This file handles:
 * 1. Liking and unliking discussion posts.
 * 2. Updating Like counts without refreshing.
 * 3. Turning liked buttons green.
 * 4. Navigating back to the previous page.
 */


// ============================================================
// 1. WAIT FOR THE HTML PAGE TO LOAD
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    // ========================================================
    // 2. FIND ALL LIKE FORMS
    // ========================================================

    // Works with both group_detail.html and discussion_detail.html.
    const likeForms = document.querySelectorAll(
        ".like-form, #like-form"
    );

    // Attach an event listener to every Like form.
    likeForms.forEach(function (form) {

        form.addEventListener("submit", async function (event) {

            // Stop the browser from refreshing the page.
            event.preventDefault();

            // Find the Like button inside this form.
            const button = form.querySelector(".like-button");

            // Find the button's text.
            const label = button?.querySelector(".like-label, #like-label");

            // Identify the discussion.
            const discussionId = form.dataset.discussionId;

            // Group feed uses a unique count ID per discussion.
            // Discussion detail uses a single count ID.
            const countElement = discussionId
                ? document.getElementById("like-count-" + discussionId)
                : document.getElementById("like-count");

            // Find the appropriate error message element.
            const errorElement = discussionId
                ? document.getElementById("like-error-" + discussionId)
                : document.getElementById("like-error");

            // Stop safely if required HTML elements are missing.
            if (!button || !label || !countElement) {
                return;
            }

            // Clear previous error messages.
            if (errorElement) {
                errorElement.hidden = true;
                errorElement.textContent = "";
            }

            // Prevent repeated clicks while saving.
            button.disabled = true;

            try {

                // Send the Like request to Django.
                const response = await fetch(form.action, {

                    method: "POST",

                    // Includes Django's CSRF token.
                    body: new FormData(form),

                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },

                    credentials: "same-origin"
                });

                // Handle unsuccessful HTTP responses.
                if (!response.ok) {
                    throw new Error(
                        "Unable to update your like. Please try again."
                    );
                }

                // Read the updated Like status from Django.
                const data = await response.json();

                // Check whether the developer liked the post.
                if (data.liked) {

                    // Turn the button green.
                    button.classList.add("liked");

                    // Update accessibility information.
                    button.setAttribute("aria-pressed", "true");

                    // Change the button text.
                    label.textContent = "💚 Liked";

                } else {

                    // Remove the green background.
                    button.classList.remove("liked");

                    button.setAttribute("aria-pressed", "false");

                    // Restore the original button text.
                    label.textContent = "♡ Like";
                }

                // Update the displayed number of likes.
                countElement.textContent = data.like_count;

            } catch (error) {

                // Display an error without changing the Like state.
                if (errorElement) {
                    errorElement.textContent = error.message;
                    errorElement.hidden = false;
                }

            } finally {

                // Allow the developer to click again.
                button.disabled = false;
            }

        });

    });


    // ========================================================
    // 3. BACK BUTTONS
    // ========================================================

    // Find all Back buttons.
    const backButtons = document.querySelectorAll(
        ".page-back-button"
    );

    backButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            // Read the fallback page from the HTML button.
            const fallbackURL = button.dataset.fallbackUrl;

            // Get the previous page.
            const previousPage = document.referrer;

            if (previousPage) {

                try {

                    const previousURL = new URL(previousPage);

                    // Only use browser history when the previous
                    // page belongs to CodeView.
                    if (
                        previousURL.origin === window.location.origin &&
                        previousURL.pathname !== window.location.pathname
                    ) {
                        window.history.back();
                        return;
                    }

                } catch (error) {

                    // Invalid referrer: use the fallback below.
                }
            }

            // Navigate to the safe fallback page.
            if (fallbackURL) {
                window.location.href = fallbackURL;
            }

        });

    });

});