with open(r'C:\Users\Administrator\Desktop\画布\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Inject script before </html>
script = '''
<script>
// Inject GPT Image 2 VIP model support
(function() {
    var checkExist = setInterval(function() {
        if (typeof window !== 'undefined' && window._NANO_BANANA_FAMILIES === undefined) {
            // Try to intercept nanoBananaModeRules export
            return;
        }
        var familySelect = document.querySelector('[class*="family"] select, [class*="model"] select');
        if (familySelect || window.__NANO_INJECTED) {
            clearInterval(checkExist);
        }
    }, 200);

    // Wait for module system to be ready, then patch
    var waitForApp = setInterval(function() {
        var loader = document.getElementById('v2-initial-loader');
        if (loader && loader.style.display === 'none') {
            clearInterval(waitForApp);
            setTimeout(function() {
                // Try to find and patch family/mode controls
                patchNanoFamilyOptions();
            }, 1000);
        }
        if (!loader) clearInterval(waitForApp);
    }, 500);

    function patchNanoFamilyOptions() {
        try {
            // The model selection is in the AIGenerateNode component
            // We need to add GPT_IMAGE_2 to the family dropdown
            // Since the code is obfuscated, we'll use a mutation observer
            // to detect when model controls are rendered
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            var familyRadios = node.querySelectorAll('[class*="family"]');
                            if (familyRadios.length > 0) {
                                console.log('[GPT VIP] Family controls found');
                            }
                        }
                    });
                });
            });
            observer.observe(document.body, { childList: true, subtree: true });
            console.log('[GPT VIP] Observer installed');
        } catch(e) {
            console.warn('[GPT VIP] Error:', e);
        }
    }
})();
</script>
'''

content = content.replace('</html>', script + '\n</html>')

with open(r'C:\Users\Administrator\Desktop\画布\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected!")
