// ========================================
// CODEVIEW GROUP WORKSPACE
// Switch between Discussions, Chat,
// and Members without reloading the page.
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    // Find all sidebar links that switch workspace sections.
    const tabs = document.querySelectorAll("[data-workspace-tab]");

    // Find the main workspace content.
    const workspaceContent = document.querySelector(".workspace-content");

    // Find the discussions, chat, and members sections.
    const discussionSections = [
        document.getElementById("create-discussion"),
        document.getElementById("group-discussions")
    ];

    const chatSection = document.getElementById("group-chat");

    const membersSection = document.getElementById("group-members");

    // Find the heading and group information.
    const workspaceHeading = document.querySelector(".workspace-heading");
    const groupInformation = document.querySelector(".workspace-group-info");

    // Find the membership notice for nonmembers.
    const membershipNotice = document.querySelector(".membership-notice");


    // ========================================
    // FUNCTION: SWITCH WORKSPACE TAB
    // ========================================

    function switchTab(tabName) {

        // Check whether the selected section exists.
        if (tabName === "chat" && !chatSection) {
            return;
        }

        if (tabName === "members" && !membersSection) {
            return;
        }

        // ====================================
        // 1. HIDE ALL WORKSPACE SECTIONS
        // ====================================

        discussionSections.forEach(function (section) {

            if (section) {
                section.hidden = true;
            }

        });

        if (chatSection) {
            chatSection.hidden = true;
        }

        if (membersSection) {
            membersSection.hidden = true;
        }

        if (workspaceHeading) {
            workspaceHeading.hidden = true;
        }

        if (groupInformation) {
            groupInformation.hidden = true;
        }

        if (membershipNotice) {
            membershipNotice.hidden = true;
        }


        // ====================================
        // 2. SHOW THE SELECTED SECTION
        // ====================================

        if (tabName === "discussions") {

            discussionSections.forEach(function (section) {

                if (section) {
                    section.hidden = false;
                }

            });

            if (workspaceHeading) {
                workspaceHeading.hidden = false;
            }

            if (groupInformation) {
                groupInformation.hidden = false;
            }

            if (membershipNotice) {
                membershipNotice.hidden = false;
            }

        } else if (tabName === "chat") {

            chatSection.hidden = false;

        } else if (tabName === "members") {

            membersSection.hidden = false;

        }


        // ====================================
        // 3. UPDATE ACTIVE SIDEBAR LINK
        // ====================================

        tabs.forEach(function (tab) {

            const isActive = tab.dataset.workspaceTab === tabName;

            tab.classList.toggle("active", isActive);

            if (isActive) {
                tab.setAttribute("aria-current", "page");
            } else {
                tab.removeAttribute("aria-current");
            }

        });


        // ====================================
        // 4. SCROLL MAIN CONTENT TO TOP
        // ====================================

        if (workspaceContent) {
            workspaceContent.scrollTop = 0;
        }

    }


    // ========================================
    // FUNCTION: READ TAB FROM URL
    // ========================================

    function getTabFromURL() {

        const hash = window.location.hash;

        if (hash === "#group-chat") {
            return "chat";
        }

        if (hash === "#group-members") {
            return "members";
        }

        return "discussions";
    }


    // ========================================
    // HANDLE SIDEBAR CLICKS
    // ========================================

    tabs.forEach(function (tab) {

        tab.addEventListener("click", function (event) {

            // Prevent normal anchor navigation.
            event.preventDefault();

            // Get the selected tab name.
            const tabName = tab.dataset.workspaceTab;

            // Update the URL without reloading.
            window.history.replaceState(
                null,
                "",
                tab.getAttribute("href")
            );

            // Display the selected section.
            switchTab(tabName);

        });

    });


    // ========================================
    // HANDLE BROWSER BACK/FORWARD HASH CHANGES
    // ========================================

    window.addEventListener("hashchange", function () {
        switchTab(getTabFromURL());
    });


    // ========================================
    // DISPLAY INITIAL SECTION
    // ========================================

    switchTab(getTabFromURL());

});