/**
 * Utilities for handling dynamic content loading
 */

function clickSeeMore() {
  return new Promise(function (resolve) {
    // Find all shadow roots
    function getAllShadowRoots(root) {
      var shadows = [];
      function walk(node) {
        var shadow = node.shadowRoot;
        if (shadow) shadows.push(shadow);
        var children = node.children;
        if (children) {
          for (var i = 0; i < children.length; i++) {
            walk(children[i]);
          }
        }
      }
      walk(root);
      return shadows;
    }

    // Find clickable parent element
    function findClickableParent(el) {
      var current = el;
      while (current && current !== document.body) {
        var style = window.getComputedStyle(current);
        if (
          current.tagName === "BUTTON" ||
          current.tagName === "A" ||
          current.role === "button" ||
          current.onclick ||
          style.cursor === "pointer"
        ) {
          return current;
        }
        current = current.parentElement;
      }
      return null;
    }

    // Find all text nodes containing "see more"
    var treeWalker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function (node) {
          return node.textContent.toLowerCase().includes("see more")
            ? NodeFilter.FILTER_ACCEPT
            : NodeFilter.FILTER_REJECT;
        },
      }
    );

    var buttons = new Set();
    while (treeWalker.nextNode()) {
      var textNode = treeWalker.currentNode;
      var element = textNode.parentElement;
      var clickable = findClickableParent(element);

      if (
        clickable &&
        clickable.offsetParent &&
        window.getComputedStyle(clickable).display !== "none"
      ) {
        buttons.add(clickable);
      }
    }

    // Convert Set to Array and sort by position
    var buttonArray = Array.from(buttons);
    var button = buttonArray.sort(function (a, b) {
      var aRect = a.getBoundingClientRect();
      var bRect = b.getBoundingClientRect();
      return bRect.top - aRect.top;
    })[0];

    if (button) {
      var prevHeight = document.documentElement.scrollHeight;
      button.click();

      // Wait for new content (max 2 seconds)
      var attempts = 0;
      var maxAttempts = 20;

      function checkHeight() {
        if (attempts >= maxAttempts) {
          resolve(true);
          return;
        }

        if (document.documentElement.scrollHeight > prevHeight) {
          resolve(true);
          return;
        }

        attempts++;
        setTimeout(checkHeight, 100);
      }

      checkHeight();
    } else {
      resolve(false);
    }
  });
}
