async function createRule() {
    const ruleString = document.getElementById('rule').value;

    const response = await fetch('/create_rule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule: ruleString })
    });

    const result = await response.json();
    document.getElementById('result').innerText = result.message + ' Rule ID: ' + result.rule_id;
}

async function evaluateRule() {
    const ruleId = document.getElementById('rule_id').value;
    const userData = {
        age: parseInt(document.getElementById('age').value),
        department: document.getElementById('department').value,
        salary: parseInt(document.getElementById('salary').value),
        experience: parseInt(document.getElementById('experience').value)
    };

    const response = await fetch(`/evaluate_rule/${ruleId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    });

    const result = await response.json();
    document.getElementById('evaluation_result').innerText = 'Evaluation Result: ' + result.result;
}
