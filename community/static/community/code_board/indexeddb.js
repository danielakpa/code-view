/**
 * CodeView — IndexedDB Storage
 *
 * Stores developers' source files inside their browsers.
 *
 * Source code is NOT sent to PostgreSQL.
 *
 * Each file belongs to a specific developer and group.
 */

// ============================================================
// 1. DATABASE SETTINGS
// ============================================================

const CODEVIEW_DB_NAME = "CodeViewWorkspace";
const CODEVIEW_DB_VERSION = 1;
const CODEVIEW_FILES_STORE = "files";


// ============================================================
// 2. OPEN THE DATABASE
// ============================================================

function openCodeViewDatabase() {

    return new Promise((resolve, reject) => {

        // Check whether the browser supports IndexedDB.
        if (!window.indexedDB) {
            reject(new Error("IndexedDB is not supported."));
            return;
        }

        // Open the database or create it if necessary.
        const request = indexedDB.open(
            CODEVIEW_DB_NAME,
            CODEVIEW_DB_VERSION
        );

        // Runs when the database is created or upgraded.
        request.onupgradeneeded = (event) => {

            const database = event.target.result;

            // Create the files store only if it doesn't exist.
            if (!database.objectStoreNames.contains(
                CODEVIEW_FILES_STORE
            )) {

                const store = database.createObjectStore(
                    CODEVIEW_FILES_STORE,
                    {
                        keyPath: "id",
                    }
                );

                // Find files belonging to a particular workspace.
                store.createIndex(
                    "workspaceId",
                    "workspaceId",
                    {
                        unique: false,
                    }
                );
            }
        };

        // Return the opened database.
        request.onsuccess = () => {
            resolve(request.result);
        };

        // Report database errors.
        request.onerror = () => {
            reject(request.error);
        };

    });
}


// ============================================================
// 3. SAVE OR UPDATE A FILE
// ============================================================

async function saveCodeViewFile(file) {

    const database = await openCodeViewDatabase();

    return new Promise((resolve, reject) => {

        // Start a transaction that allows writing.
        const transaction = database.transaction(
            CODEVIEW_FILES_STORE,
            "readwrite"
        );

        const store = transaction.objectStore(
            CODEVIEW_FILES_STORE
        );

        // Save the file or update an existing file.
        store.put(file);

        transaction.oncomplete = () => {
            database.close();
            resolve(file);
        };

        transaction.onerror = () => {
            database.close();
            reject(transaction.error);
        };

        transaction.onabort = () => {
            database.close();
            reject(transaction.error);
        };

    });
}


// ============================================================
// 4. GET ALL FILES IN A WORKSPACE
// ============================================================

async function getCodeViewFiles(workspaceId) {

    const database = await openCodeViewDatabase();

    return new Promise((resolve, reject) => {

        // Read-only transaction.
        const transaction = database.transaction(
            CODEVIEW_FILES_STORE,
            "readonly"
        );

        const store = transaction.objectStore(
            CODEVIEW_FILES_STORE
        );

        // Search only files belonging to this workspace.
        const index = store.index("workspaceId");

        const request = index.getAll(workspaceId);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };

        transaction.oncomplete = () => {
            database.close();
        };

        transaction.onerror = () => {
            database.close();
        };

    });
}


// ============================================================
// 5. GET ONE FILE
// ============================================================

async function getCodeViewFile(fileId) {

    const database = await openCodeViewDatabase();

    return new Promise((resolve, reject) => {

        const transaction = database.transaction(
            CODEVIEW_FILES_STORE,
            "readonly"
        );

        const store = transaction.objectStore(
            CODEVIEW_FILES_STORE
        );

        const request = store.get(fileId);

        request.onsuccess = () => {
            resolve(request.result || null);
        };

        request.onerror = () => {
            reject(request.error);
        };

        transaction.oncomplete = () => {
            database.close();
        };

        transaction.onerror = () => {
            database.close();
        };

    });
}


// ============================================================
// 6. DELETE A FILE
// ============================================================

async function deleteCodeViewFile(fileId) {

    const database = await openCodeViewDatabase();

    return new Promise((resolve, reject) => {

        const transaction = database.transaction(
            CODEVIEW_FILES_STORE,
            "readwrite"
        );

        const store = transaction.objectStore(
            CODEVIEW_FILES_STORE
        );

        store.delete(fileId);

        transaction.oncomplete = () => {
            database.close();
            resolve();
        };

        transaction.onerror = () => {
            database.close();
            reject(transaction.error);
        };

        transaction.onabort = () => {
            database.close();
            reject(transaction.error);
        };

    });
}


// ============================================================
// 7. MAKE STORAGE FUNCTIONS AVAILABLE
// ============================================================

window.CodeViewStorage = {

    openDatabase: openCodeViewDatabase,

    saveFile: saveCodeViewFile,

    getFiles: getCodeViewFiles,

    getFile: getCodeViewFile,

    deleteFile: deleteCodeViewFile,

};