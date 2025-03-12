/**
 * Utilities for scrolling and content loading
 */
function sleep(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

function scrollPage() {
  return new Promise(function (resolve) {
    (function scroll() {
      var lastHeight = 0;
      var unchanged = 0;
      var maxUnchanged = 3;

      // Keep scrolling until height stops changing
      function tryScroll() {
        window.scrollTo(0, document.body.scrollHeight);

        sleep(1000).then(function () {
          var currentHeight = document.body.scrollHeight;
          console.log("Scroll height:", currentHeight);

          if (currentHeight === lastHeight) {
            unchanged++;
          } else {
            unchanged = 0;
          }
          lastHeight = currentHeight;

          // Also check network activity
          var entries = window.performance.getEntriesByType("resource");
          var recentEntries = entries.filter(function (e) {
            return (
              Date.now() - e.startTime < 2000 && e.initiatorType !== "script"
            );
          });
          console.log("Recent network requests:", recentEntries.length);

          if (recentEntries.length > 0) {
            unchanged = 0; // Reset if still loading
          }

          if (unchanged < maxUnchanged) {
            tryScroll();
          } else {
            window.scrollTo(0, 0);
            sleep(1000).then(resolve);
          }
        });
      }

      tryScroll();
    })();
  });
}
