"use strict";

/*
========================================================
CODEVIEW - DISCUSSION INTERACTIONS
========================================================

Responsibilities:

1. Handle the Back button.
2. Send Like/Unlike requests to Django.
3. Update the Like button without refreshing.
4. Update the number of likes.
5. Display errors when requests fail.

This JavaScript can be reused on multiple pages.
*/

document.addEventListener("DOMContentLoaded", () => {

    // ====================================================
    // 1. BACK BUTTON
    // ====================================================

    // Find all Back buttons on the page.
    const backButtons = document.querySelectorAll(
        ".page-back-button"
    );

    // Attach a click event to each Back button.
    backButtons.forEach(function(button) {

        button.addEventListener("click", function() {

            // Read the fallback URL stored in the HTML.
            const fallbackURL = button.dataset.fallbackUrl || "/";

            // Get the page the developer came from.
            const previousPage = document.referrer;

            if (previousPage) {

                try {

                    // Convert the previous address into a URL object.
                    const previousURL = new URL(previousPage);

                    // Only go back if the previous page belongs
                    // to CodeView and is different from this page.
                    if (
                        previousURL.origin === window.location.origin &&
                        previousURL.pathname !== window.location.pathname
                    ) {

                        window.history.back();

                        return;
                    }

                } catch (error) {

                    // If the previous URL is invalid,
                    // continue to the fallback below.
                }
            }

            // Open the groups dashboard if going back is unsafe.
            window.location.href = fallbackURL;

        });

    });


    // ====================================================
    // 2. FIND DISCUSSION LIKE FORMS
    // ====================================================

    // Find Like forms on the group and discussion pages.
    const likeForms = document.querySelectorAll(
        ".like-form, #like-form"
    );

    // Give each Like form its own submit event.
    likeForms.forEach(function(form) {

        form.addEventListener("submit", async function(event) {

            // Stop the browser from reloading the page.
            event.preventDefault();


            // ====================================================
            // 3. FIND THE DISCUSSION ELEMENTS
            // ====================================================

            // Get the discussion ID stored in the form.
            const discussionId = form.dataset.discussionId;

            // Find the Like button.
            const button = form.querySelector(".like-button");

            // Stop if the button does not exist
            // or a request is already processing.
            if (!button || button.disabled) {
                return;
            }

            // Find the text inside the Like button.
            const label = button.querySelector(".like-label");

            // Find the Like count for this discussion.
            const countElement = discussionId
                ? document.getElementById(
                    "like-count-" + discussionId
                )
                : document.querySelector("#like-count");

            // Find the container for displaying errors.
            const errorElement = discussionId
                ? document.getElementById(
                    "like-error-" + discussionId
                )
                : document.querySelector("#like-error");


            // ====================================================
            // 4. PREPARE THE REQUEST
            // ====================================================

            // Clear any previous error message.
            if (errorElement) {

                errorElement.hidden = true;

                errorElement.textContent = "";
            }

            // Prevent repeated clicks while Django saves the Like.
            button.disabled = true;


            // ====================================================
            // 5. SEND REQUEST TO DJANGO
            // ====================================================

            try {

                // Send a POST request to the form's Django URL.
                const response = await fetch(form.action, {

                    method: "POST",

                    // Include form values and Django's CSRF token.
                    body: new FormData(form),

                    // Tell Django this is an AJAX request.
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },

                    // Include cookies for this website.
                    credentials: "same-origin"

                });


                // Stop if Django returns an error.
                if (!response.ok) {

                    throw new Error(
                        "Unable to update your like. Please try again."
                    );
                }


                // ====================================================
                // 6. READ DJANGO'S RESPONSE
                // ====================================================

                // Convert Django's JSON response into a JS object.
                const data = await response.json();


                // ====================================================
                // 7. UPDATE THE LIKE BUTTON
                // ====================================================

                if (data.liked) {

                    // Make the button green.
                    button.classList.add("liked");

                    // Mark the button as pressed for accessibility.
                    button.setAttribute("aria-pressed", "true");

                    // Change the button text.
                    if (label) {
                        label.textContent = "💚 Liked";
                    }

                } else {

                    // Remove the green appearance.
                    button.classList.remove("liked");

                    // Mark the button as not pressed.
                    button.setAttribute("aria-pressed", "false");

                    // Change the button text.
                    if (label) {
                        label.textContent = "♡ Like";
                    }
                }


                // ====================================================
                // 8. UPDATE THE LIKE COUNT
                // ====================================================

                // Use the number returned by Django.
                if (countElement) {

                    countElement.textContent = data.like_count;
                }


            } catch (error) {

                // ====================================================
                // 9. HANDLE REQUEST ERRORS
                // ====================================================

                if (errorElement) {

                    // Show the error to the developer.
                    errorElement.textContent = error.message;

                    errorElement.hidden = false;

                } else {

                    // Log errors when no error container exists.
                    console.error(
                        "CodeView Like request failed:",
                        error
                    );
                }

            } finally {

                // ====================================================
                // 10. ENABLE THE BUTTON AGAIN
                // ====================================================

                // Allow another Like/Unlike request.
                button.disabled = false;
            }

        });

    });

});