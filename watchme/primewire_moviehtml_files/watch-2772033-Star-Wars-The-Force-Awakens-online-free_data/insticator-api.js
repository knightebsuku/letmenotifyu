

(function () {
    'use strict';
    var embedUUID;
    if (typeof insticator_embedUUID !== 'undefined') {
        embedUUID = insticator_embedUUID;
    }
    else {
        embedUUID = instciator_WidgetSettingUUID;
    }


    // Check for duplicated iframes, and remove it.

    var asyncContainers = window.parent.document.querySelectorAll("[id='insticator-api-iframe-div']");
    var syncContainers = document.querySelectorAll("[id='insticator-api-div']");

    if(asyncContainers.length > 1) {
        asyncContainers[asyncContainers.length - 1].remove();
        window.parent.document.getElementById("insticatorIframe").remove();
        return;
    }

    if(syncContainers.length > 1) {
        syncContainers[syncContainers.length - 1].remove();
        return;
    }

    if(syncContainers.length && asyncContainers.length) {
        syncContainers[syncContainers.length - 1].remove();
        return;
    }

    /**Setting need to be done for the Async Code.*/
    if(typeof insticatorAsync !== "undefined" && insticatorAsync) {
        //  console.log("preparing document for async");
        var insticatorDiv = document.createElement('div');
        insticatorDiv.setAttribute("id","insticator-api-div");
        document.body.appendChild(insticatorDiv);

        document.body.style.cssText = "margin:auto;";
        var iFrame = window.parent.document.getElementById('insticatorIframe');
        if (iFrame) {
            iFrame.style.cssText = "max-width:1200px;width:100%;min-width:160px;height:0px;";
        }
    }


    var script = document.createElement('script');
    var hostName = "https://embed.insticator.com";
    script.src = hostName + "/embeds/getembed" +
        "?embedUUID=" + embedUUID +
        "&servedOnUrl=" + encodeURIComponent(document.location) +
        "&callback=insticatorEmbedCallback";
    document.getElementsByTagName('head')[0].appendChild(script);

    processEmbedServed(embedUUID, hostName, window.parent, window.parent.document);



    function processEmbedServed(embedUUID, hostName, window, document) {
        "use strict";

        function getCmsUsed() {
            var metas = document.getElementsByTagName('meta');

            function getMetaContent(strProperty) {
                var metaString = "";

                for (var i = 0; i < metas.length; i++) {
                    if (metas[i].getAttribute("name") == strProperty || metas[i].getAttribute("property") == strProperty) {
                        metaString += metas[i].getAttribute("content");
                    }
                }
                return metaString;
            }

            function detectCMS(strGenerator) {

                if (strGenerator.length < 1) {
                    return 'undefined';
                } else {

                    if (strGenerator.toLowerCase().indexOf("contao") > -1) {
                        return 'contao';
                    }
                    if (strGenerator.toLowerCase().indexOf("wordpress") > -1) {
                        return 'wordpress';
                    }
                    if (strGenerator.toLowerCase().indexOf("joomla") > -1) {
                        return 'joomla';
                    }
                    if (strGenerator.toLowerCase().indexOf("drupal") > -1) {
                        return 'drupal';
                    }
                    if (strGenerator.toLowerCase().indexOf("typo3") > -1) {
                        return 'typo3';
                    }
                    if (strGenerator.toLowerCase().indexOf("blogger") > -1) {
                        return 'blogger';
                    }

                    return 'undefined';
                }
            }

            var metaString_generator = getMetaContent('generator');
            if (metaString_generator === "") {
                metaString_generator = getMetaContent('Generator');
            }
            return detectCMS(metaString_generator);
        }

        function getEmbedCodeVersion() {

            function getVersion() {
                if (typeof window.Insticator !== "undefined") {
                    return window.Insticator.version ? window.Insticator.version : "1.0";
                } else {
                    return "1.0";
                }
            }

            function getType() {
                if (document.getElementById("insticator-api-iframe-div")) {
                    return "Asynchronous";
                } else if (document.getElementById("insticator-api-div")) {
                    return "Synchronous";
                } else {
                    return "Undefined";
                }
            }

            var version = getVersion();

            if(version == "1.0"){
                return version  + "_" + getType();
            }
            else{
                return version;
            }
        }

        function getAsUriString(jsonObject) {
            return Object.keys(jsonObject).map(function (key) {
                return encodeURIComponent(key) + '=' + encodeURIComponent(jsonObject[key]);
            }).join('&');
        }

        function sendData() {
            try {
                var data = {
                    cms: getCmsUsed(),
                    embedCodeVersion: getEmbedCodeVersion(),
                    servedOnUrl: document.location,
                    embedUUID : embedUUID
                };

                var queryString = getAsUriString(data);

                var script = document.createElement('script');
                script.src = hostName + "/embeds/processembedserved?" + queryString;
                script.async = true;
                document.getElementsByTagName('head')[0].appendChild(script);

            } catch (e) {
                console.log(e);
            }
        }

        var domReady = function (callback) {
            document.readyState === "interactive" || document.readyState === "complete" ? callback() : document.addEventListener("DOMContentLoaded", callback);
        };

        try {
            if (embedUUID && hostName) {
                domReady(sendData);
            }
        } catch (err) {
            console.log(err);
            return "";
        }
    }

})();

function insticatorEmbedCallback(data) {
    'use strict';
    var embed = data;
    if (embed != null && embed.isActivate) {
        if (embed.embedSetting.showDisplay) {
            createElement("IFRAME", {
                src: insticatorGetDomainLocation(false) + '/embeds/displayAd?embedUUID=' + embed.embedUUID + '&adPosition=1',
                class: "displayAds",
                id: "displayAds1",
                style: "width:100%;height:0px;margin:auto;display:block",
                frameborder: 0,
                scrolling: "no"
            }, "insticator-api-div");
        }

        if (embed.embedSetting.showVideoAd) {
            createElement("IFRAME", {
                src: insticatorGetDomainLocation(false) + '/embeds/videoAd?embedUUID=' + embed.embedUUID,
                class: "displayAds",
                id: "displayAdsVideo",
                style: "width:100%;height:1px;margin:auto;display:block",
                frameborder: 0,
                scrolling: "no"
            }, "insticator-api-div");
        }

        console.log("ok"+new Date().getTime());
        createElement("IFRAME", {
            src: insticatorGetDomainLocation(true) + '/embeds/getapiembed?embedUUID=' + embed.embedUUID,
            name: "insticator-api",
            id: "insticator-api-content",
            style: "display:block;margin:auto;max-width:1200px;width:100%;min-width:160px;height:0px;",
            frameborder: 0,
            scrolling: "no"
        }, "insticator-api-div");


        if (embed.embedSetting.showDisplay2) {
            createElement("IFRAME", {
                src: insticatorGetDomainLocation(false) + '/embeds/displayAd?embedUUID=' + embed.embedUUID + '&adPosition=2',
                class: "displayAds",
                id: "displayAds2",
                style: "width:100%;height:0px;margin:auto;display:block",
                frameborder: 0,
                scrolling: "no"
            }, "insticator-api-div");
        }
    }

    function createElement(type, data, targetID) {
        var element = document.createElement(type);
        for (var property in data) {
            element.setAttribute(property, data[property]);
        }
        document.getElementById(targetID).appendChild(element);
    }

    function insticatorGetDomainLocation(forceSSL) {
        if (forceSSL) {
            return "https://embed.insticator.com";
        }
        return ('https:' === window.location.protocol ? 'https://' : 'http://') + "embed.insticator.com";
    }

    window.addEventListener("message", executeAction, false);
}


function executeAction(e) {
    'use strict';
    if (e.origin.indexOf("embed.insticator.com") >= 0) // for security: set this to the domain of the iframe - use e.uri if you need more specificity
    {
        switch (e.data.action) {
            case "resize":

                document.getElementById(e.data.id).style.height = e.data.height + "px";
                if (typeof e.data.width != "undefined" && typeof e.data.width != null) {
                    document.getElementById(e.data.id).style.width = e.data.width + "px";
                }

                if(typeof insticatorAsync !== "undefined" && insticatorAsync) {
                    /**Changing the height for container Iframe and div*/
                    var iFrame = window.parent.document.getElementById('insticatorIframe');
                    var iFrameParentDiv = window.parent.document.getElementById('insticator-api-iframe-div');
                    if (iFrameParentDiv && iFrame) {
                        var  height = document.getElementById('insticator-api-div').scrollHeight;
                        //                        console.log("Got div height : " +  height+ "px");
                        iFrameParentDiv.style.height =height + "px";
                        iFrame.style.height = height + "px";
                    }
                }

                break;
            case "refresh":
                if(document.getElementById(e.data.id)) {
                    document.getElementById(e.data.id).src = document.getElementById(e.data.id).src;
                }
                break;
            case "socialShare":
                postAction("socialShare", "insticator-api-content");
                break;
            case "customAction":
                eval('(' + decodeURI(e.data.id) + ')();');
                break;
            case "refreshAd":
                if(typeof insticatorAsync !== "undefined" && insticatorAsync) {
                    postActionToPartnerSite("refreshAd");
                }
                break;
        }
    }
}
function postAction(action, divId) {
    'use strict';
    var target = document.getElementById(divId).contentWindow;
    var postContent = {
        action: action,
        id: divId,
        domain: window.location.href
    };
    target.postMessage(postContent, "*");
}

function postActionToPartnerSite(action) {
    'use strict';
    var postContent = {
        action: action,
        domain: window.location.href
    };
    parent.postMessage(postContent, "*");
}
