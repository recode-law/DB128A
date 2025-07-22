function onReasonChange(select, court_id) {
    let box = document.getElementById(`court-${court_id}-otherReasonBox`);
    if (select.value === "other") {
        box.innerHTML = `<label for="court-${court_id}-otherReason" class="form-label">Sonstiger Grund:</label>` +
            `<input type="text" class="form-control" id="court-${court_id}-otherReason" name="otherReason" required oninput="onOtherReasonChange(this, ${court_id});">` +
            `<div id="court-${court_id}-otherReasonRemainder" class="form-text">40 Zeichen übrig</div>`;
    } else {
        box.innerHTML = "";
    }
}

function onOtherReasonChange(input, court_id) {
    input.value = input.value.substring(0, 40);
    document.getElementById(`court-${court_id}-otherReasonRemainder`).innerHTML = `${40-input.value.length} Zeichen übrig`;
}