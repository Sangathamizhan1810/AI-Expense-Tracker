/**
 * AI Expense Tracker — Quick Add Playwright Test Suite
 *
 * Covers all scenarios for the Quick Add expense adder modal:
 * - TC-01: Modal Open/Close & Keyboard Shortcuts
 * - TC-02: Suggestion Chips Pre-filling
 * - TC-03: Input Sanitization (Alphabet & Numerical filtering)
 * - TC-04: Clear Button Reset Behavior
 * - TC-05: AI Categorization Trigger & Live Preview
 * - TC-06: 1-Tap Pill Editing (Category & Date)
 * - TC-07: Expense Submission & Persistence in Ledger
 */

import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:5000';
const TEST_EMAIL = process.env.TEST_EMAIL || 'sanga@gmail.com';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'password123';

async function runTests() {
    console.log('🚀 Launching Playwright browser...');
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    let passedCount = 0;
    let failedCount = 0;

    function assert(condition, message) {
        if (!condition) {
            failedCount++;
            console.error(`  ❌ FAIL: ${message}`);
            throw new Error(message);
        } else {
            passedCount++;
            console.log(`  ✅ PASS: ${message}`);
        }
    }

    try {
        // --- Setup: Sign in ---
        console.log(`\n🔑 Signing in at ${BASE_URL}/auth/login...`);
        await page.goto(`${BASE_URL}/auth/login?next=/expenses/`);
        await page.locator('input[name="email"]').fill(TEST_EMAIL);
        await page.locator('input[name="password"]').fill(TEST_PASSWORD);
        await page.locator('button:has-text("Sign In")').click();
        await page.waitForURL('**/expenses/**');
        console.log('  ✅ Successfully authenticated into financial terminal.');

        // ----------------------------------------------------
        // TC-01: Modal Open & Close Lifecycle
        // ----------------------------------------------------
        console.log('\n🧪 TC-01: Modal Open & Close Lifecycle');
        await page.locator('button.cmd-trigger-btn.js-open-cmd').click();
        
        let isOpen = await page.locator('#cmd-palette-backdrop').evaluate(el => el.classList.contains('open'));
        assert(isOpen === true, 'Quick Add modal opened on trigger click');

        const initialDesc = await page.locator('#cmd-input-desc').inputValue();
        const initialAmt = await page.locator('#cmd-input-amt').inputValue();
        assert(initialDesc === '' && initialAmt === '', 'Input fields initialize empty');

        const suggestionsVisible = await page.locator('#cmd-suggestions').isVisible();
        assert(suggestionsVisible === true, 'Suggestions chips are visible when inputs are empty');

        // Test Escape key closes modal
        await page.keyboard.press('Escape');
        isOpen = await page.locator('#cmd-palette-backdrop').evaluate(el => el.classList.contains('open'));
        assert(isOpen === false, 'Escape key cleanly dismisses modal');

        // Re-open for subsequent tests
        await page.locator('button.cmd-trigger-btn.js-open-cmd').click();

        // ----------------------------------------------------
        // TC-02: Suggestion Chips Pre-filling
        // ----------------------------------------------------
        console.log('\n🧪 TC-02: Suggestion Chips Pre-filling');
        const chip = page.locator('button.cmd-suggest-chip:has-text("Swiggy 350")');
        await chip.click();

        const chipDesc = await page.locator('#cmd-input-desc').inputValue();
        const chipAmt = await page.locator('#cmd-input-amt').inputValue();
        assert(chipDesc === 'Swiggy', 'Description populated with "Swiggy"');
        assert(chipAmt === '350', 'Amount populated with "350"');

        const quickAddVisible = await page.locator('#cmd-quick-add-btn').isVisible();
        assert(quickAddVisible === true, 'Quick add button appears when both fields populated');

        const clearBtnVisible = await page.locator('#cmd-clear-btn').isVisible();
        assert(clearBtnVisible === true, 'Clear button appears when inputs have content');

        // ----------------------------------------------------
        // TC-04: Clear Button Reset Behavior
        // ----------------------------------------------------
        console.log('\n🧪 TC-04: Clear Button Reset Behavior');
        await page.locator('#cmd-clear-btn').click();

        const clearedDesc = await page.locator('#cmd-input-desc').inputValue();
        const clearedAmt = await page.locator('#cmd-input-amt').inputValue();
        assert(clearedDesc === '' && clearedAmt === '', 'Inputs cleared on clear button click');

        const quickAddHidden = !(await page.locator('#cmd-quick-add-btn').isVisible());
        assert(quickAddHidden === true, 'Quick add button hidden after clearing');

        const suggestionsReturned = await page.locator('#cmd-suggestions').isVisible();
        assert(suggestionsReturned === true, 'Suggestion chips returned');

        // ----------------------------------------------------
        // TC-03: Real-time Input Sanitization
        // ----------------------------------------------------
        console.log('\n🧪 TC-03: Real-time Input Sanitization');
        // Type alphabets + numbers + special characters in description
        await page.locator('#cmd-input-desc').fill('Dinner 999 @#$');
        const sanitizedDesc = await page.locator('#cmd-input-desc').inputValue();
        assert(sanitizedDesc.trim() === 'Dinner' && !/[0-9@#$]/.test(sanitizedDesc), 'Description strips non-alphabet characters');

        // Type mixed letters + numbers + extra dots in amount
        await page.locator('#cmd-input-amt').fill('abc 850.50.25');
        const sanitizedAmt = await page.locator('#cmd-input-amt').inputValue();
        assert(sanitizedAmt === '850.5025', 'Amount strips non-numeric characters and extra dots');

        // ----------------------------------------------------
        // TC-05: AI Categorization Trigger & Live Preview
        // ----------------------------------------------------
        console.log('\n🧪 TC-05: AI Categorization Trigger & Live Preview');
        await page.locator('#cmd-input-desc').fill('Metro Card Recharge');
        await page.locator('#cmd-input-amt').fill('200');

        // Trigger AI classification
        await page.locator('#cmd-quick-add-btn').click();

        // Wait for preview container to appear
        await page.waitForSelector('#cmd-result-container', { state: 'visible', timeout: 10000 });
        
        const previewAmt = await page.locator('#cmd-result-amount').innerText();
        const previewNote = await page.locator('#cmd-result-note').innerText();
        const categoryPill = await page.locator('#cmd-category-text').innerText();
        const saveBtnEnabled = await page.locator('#cmd-submit-btn').isEnabled();

        assert(previewAmt.includes('200.00'), 'Preview displays formatted amount ₹200.00');
        assert(previewNote === 'Metro Card Recharge', 'Preview displays description');
        assert(categoryPill.length > 0, `AI categorized transaction as "${categoryPill}"`);
        assert(saveBtnEnabled === true, 'Primary "Save expense" button is enabled');

        // ----------------------------------------------------
        // TC-06: 1-Tap Pill Editing (Category & Date)
        // ----------------------------------------------------
        console.log('\n🧪 TC-06: 1-Tap Pill Editing (Category & Date)');
        // Change category to Bills (id = 4)
        await page.locator('#cmd-category-select').selectOption('4');
        const updatedCatPill = await page.locator('#cmd-category-text').innerText();
        const hiddenCatId = await page.locator('#cmd-hidden-category-id').inputValue();
        assert(updatedCatPill === 'Bills', 'Category pill visual text updated to "Bills"');
        assert(hiddenCatId === '4', 'Hidden category form input updated to "4"');

        // ----------------------------------------------------
        // TC-07: Expense Submission & Persistence in Ledger
        // ----------------------------------------------------
        console.log('\n🧪 TC-07: Expense Submission & Persistence');
        await page.locator('#cmd-submit-btn').click();
        await page.waitForURL('**/expenses/**');

        const firstRowText = await page.locator('.data-table tbody tr').first().innerText();
        assert(firstRowText.includes('Metro Card Recharge'), 'New expense note found in table ledger');
        assert(firstRowText.includes('200.00'), 'New expense amount found in table ledger');
        assert(firstRowText.includes('Bills'), 'New expense category (Bills) found in table ledger');

        // ----------------------------------------------------
        // TC-08: User Test Case - Editing Input After AI Answer Resets Button to "Quick add"
        // ----------------------------------------------------
        console.log('\n🧪 TC-08: Editing Text Input After AI Answer Resets Button to "Quick add"');
        // Re-open Quick Add modal
        await page.locator('button.cmd-trigger-btn.js-open-cmd').click();
        await page.locator('#cmd-input-desc').fill('Coffee');
        await page.locator('#cmd-input-amt').fill('150');

        // Click Quick add to trigger AI classification
        await page.locator('#cmd-quick-add-btn').click();
        await page.waitForSelector('#cmd-result-container', { state: 'visible', timeout: 10000 });
        
        // AI generated answer
        const coffeePreviewVisible = await page.locator('#cmd-result-container').isVisible();
        assert(coffeePreviewVisible === true, 'AI successfully generated answer and displayed preview');

        // Now, as a user, edit the text input field (e.g. typing 'ww')
        await page.locator('#cmd-input-desc').fill('ww');

        // Assert button is visible and displays "Quick add", NOT "AI Categorizing..."
        const btnVisibleAfterEdit = await page.locator('#cmd-quick-add-btn').isVisible();
        const btnTextAfterEdit = (await page.locator('#cmd-quick-add-btn').innerText()).trim();
        const btnHtmlAfterEdit = await page.locator('#cmd-quick-add-btn').innerHTML();

        assert(btnVisibleAfterEdit === true, 'Button is visible after editing text field');
        assert(btnTextAfterEdit.includes('Quick add'), `Button says "Quick add" (Actual: "${btnTextAfterEdit}")`);
        assert(!btnHtmlAfterEdit.includes('AI Categorizing'), 'Button does NOT say "AI Categorizing..."');
        assert(!btnHtmlAfterEdit.includes('⏳'), 'Button does NOT show hourglass/loading state');

        // Close modal
        await page.keyboard.press('Escape');

        console.log(`\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!`);
        console.log(`Summary: ${passedCount} assertions passed, ${failedCount} failed.`);
    } catch (err) {
        console.error('\n❌ Test Suite Aborted with Error:', err.message);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
}

runTests();
