const form = document.getElementById("query-form");
const input = document.getElementById("query-input");
const answer = document.getElementById("answer");
const button = form.querySelector("button");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = input.value.trim();

    if (!query) return;

    // Show question
    answer.innerHTML = `
        <div class="question">
            ${query}
        </div>

        <div class="response"></div>
    `;

    const responseElement = answer.querySelector(".response");

    // Disable input while generating
    input.disabled = true;
    button.disabled = true;
    button.textContent = "Thinking...";

    try {
        const response = await fetch(
            "http://localhost:8000/query/stream",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query: query
                })
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, {
                stream: true
            });

            const events = buffer.split("\n\n");

            buffer = events.pop();

            for (const event of events) {
                if (!event.startsWith("data:")) continue;

                const data = event
                    .replace(/^data:\s*/, "")
                    .trim();

                if (!data) continue;

                const parsed = JSON.parse(data);

                if (parsed.type === "token") {
                    responseElement.textContent += parsed.content;
                }
            }
        }

    } catch (error) {
        console.error(error);

        responseElement.textContent =
            "Something went wrong.";
    }

    // Re-enable
    input.disabled = false;
    button.disabled = false;
    button.textContent = "Ask";

    input.value = "";
    input.focus();
});