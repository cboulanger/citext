/**
 * Code to copy & pase into the Zotero Developer "Run Javascript" Console
 * until it is integrated in a Zotero Add-in
 */

/*global Zotero */

const zoteroOverlay = {
    init: function () {
        /*** START COPY ***/
        /**
         * Validates JSON POST object against a validation map of validator functions.
         * Unless the validation functions returns true, an error is thrown.
         * @param {{[key:string]:any}} args
         * @param {{[key:string]:function}} argsValidatorMap
         * @param {string?} msg Optional informational message about the required value type
         */
        function validatePostData(args, argsValidatorMap, msg = "") {
            for (let [argName, argValidator] of Object.entries(argsValidatorMap)) {
                let errMsg;
                if (args[argName] === undefined) {
                    errMsg = `Missing value for ${argName}`;
                } else {
                    let result = argValidator(args[argName]);
                    switch (result) {
                        case true:
                            continue;
                        case false:
                            errMsg = `Invalid value for ${argName}`;
                            break;
                        default:
                            errMsg = result;
                    }
                }
                if (msg) errMsg += ": " + msg;
                throw new Error(errMsg);
            }
        }

        /**
         * Returns an array with data on the accessible libraries, e.g.
         * ```
         * [
         *     {"libraryID":1,"libraryType":"user"},
         *     {"libraryID":12345,"libraryType":"group","groupID":987654,"groupName":"My Group"}
         * ]
         * ```
         */
        Zotero.Server.Endpoints["/zotero-cita/getLibraryData"] = function () {
            return {
                supportedMethods: ["GET"],
                init: function (data, sendResponseCallback) {
                    try {
                        let libraryData = Zotero.Libraries.getAll().map(l => ({
                            libraryID: l._libraryID,
                            libraryType: l._libraryType,
                            groupID: l._groupID,
                            groupName: l._groupName
                        }));
                        sendResponseCallback(200, "application/json", JSON.stringify(libraryData));
                    } catch (error) {
                        sendResponseCallback(404, "text/plain", `Error occurred:\n${error}`);
                    }
                }
            }
        }

        /**
         * Create or more items in the given library which can later be linked. JSON POST data
         * must contain the following top-level fields:
         * `libraryID` (int)
         * `collectionID` (string|null) If not null, the collection key which will be added to each newly created
         * entry
         * `items` (array) Either an array of zotero json item data or a string containing one or more items in
         * a format that can be recognized and translated by Zotero.
         * Returns the keys of the created items
         */
        Zotero.Server.Endpoints["/zotero-cita/create"] = function () {
            return {
                supportedMethods: ["POST"],
                init: async function (postData, sendResponseCallback) {
                    try {
                        validatePostData(postData, {
                            libraryID: val => typeof val == "number" && parseInt(val, 10) === val,
                            collections: val => val === null || Array.isArray(val),
                            items: val => val && typeof val == "string" || Array.isArray(val) && val.length > 0
                        }, "libraryID: int, collections: array|null, items: object[]|string");
                        let {libraryID, collections, items} = postData;

                        if (items[0] && typeof items[0] == "object" && items[0].itemType !== undefined) {
                            // items in Zotero-JSON
                            let itemIds = [];
                            for (let itemData of items) {
                                const item = new Zotero.Item(itemData.itemType);
                                item.libraryID = libraryID;
                                for (let [key, value] of Object.entries(itemData)) {
                                    switch (key) {
                                        case "itemType":
                                        case "key":
                                        case "version":
                                            // ignore
                                            break;
                                        case "creators":
                                            item.setCreators(value);
                                            break;
                                        case "tags":
                                            item.setTags(value);
                                            break;
                                        case "collections":
                                            if (collections) {
                                                // if collection id is given, add to existing ones
                                                value = value.concat(collections)
                                            }
                                            item.setCollections(value);
                                            break;
                                        case "relations":
                                            item.setRelations(value);
                                            break;
                                        default:
                                            item.setField(key, value);
                                    }
                                }
                                let itemID = await item.saveTx();
                                itemIds.push(itemID);
                            }
                            items = await Zotero.Items.getAsync(itemIds);
                        } else if (typeof items == "string") {
                            // Import items via translators
                            // adapted from https://github.com/zotero/zotero/blob/master/chrome/content/zotero/xpcom/connector/server_connector.js#L1416
                            let translate = new Zotero.Translate.Import();
                            translate.setString(items);
                            let translators = await translate.getTranslators();
                            if (!translators || !translators.length) {
                                throw new Error("No translator could be found for input data.");
                            }
                            translate.setTranslator(translators[0]);
                            items = await translate.translate({
                                libraryID,
                                collections,
                                forceTagType: 1,
                                // Import translation skips selection by default, so force it to occur
                                saveOptions: {
                                    skipSelect: false
                                }
                            });
                        } else {
                            throw new Error("Invalid items data");
                        }
                        let itemKeys = items.map(item => item.key);
                        sendResponseCallback(200, "application/json", JSON.stringify(itemKeys));
                    } catch (error) {
                        sendResponseCallback(404, "text/plain", `Error occurred:\n${error}`);
                    }
                }
            }
        }

        /**
         * Given a `libraryID` and a `query`, depending on the `resultType`,
         * return either an array of "items" matching the query,
         * an array of item "keys" or the number of "hits".
         * Example POST data:
         * ```
         * {
         * 	    "libraryID": 1,
         * 	    "query": {
         * 		    "date": ["is", "2019"],
         * 		    "title": ["contains", "zotero"]
         * 	    },
         * 	    "resultType": "items"
         * }
         * ```
         */
        Zotero.Server.Endpoints["/zotero-cita/search"] = function () {
            return {
                supportedMethods: ["POST"],
                init: async function (postData, sendResponseCallback) {
                    try {
                        validatePostData(postData, {
                            libraryID: val => typeof val == "number" && parseInt(val, 10) === val,
                            query: val => val && typeof val === "object" && Object.entries(val).length > 0,
                            resultType: val => ["items", "keys", "hits"].includes(val)
                        }, "libraryID (int), query (object), resultType ('items|keys|hits')");
                        let {libraryID, query, resultType} = postData;
                        let s = new Zotero.Search();
                        s.libraryID = libraryID;
                        for (let [field, conditions] of Object.entries(query)) {
                            if (!Array.isArray(conditions)) {
                                conditions = [conditions];
                            }
                            conditions.unshift(field);
                            s.addCondition.apply(s, conditions);
                        }
                        let results = await s.search();
                        if (resultType === "hits") {
                            sendResponseCallback(200, "application/json", String(results.length));
                            return;
                        }
                        let items = await Zotero.Items.getAsync(results);
                        if (resultType === "keys") {
                            items = items.map(item => item.key);
                        }
                        sendResponseCallback(200, "application/json", JSON.stringify(items));
                    } catch (error) {
                        sendResponseCallback(404, "text/plain", `Error occurred:\n${error}`);
                    }
                }
            }
        }
        /*** END COPY ***/
    }
};

export default zoteroOverlay;