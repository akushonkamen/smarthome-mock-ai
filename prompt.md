The virtual devices are ready. Now let's implement the "AI Brain".

Objective: Connect an LLM to control the virtual devices using Function Calling (or JSON output parsing).

Task 3: Agent Implementation & CLI
1. Create an `Agent` class. It should accept a user's natural language input (e.g., "It's too hot in here").
2. Define "Tools" or "Functions" describing our available devices (e.g., `set_temperature`, `turn_on_light`).
3. Use an LLM API (2b67595b80794ec48c41937c872e64bc.pRRVyDaLVhfbPXv4) to reason,接口文档在这里：https://docs.bigmodel.cn/api-reference/模型-api/对话补全. The LLM should decide which tool to call based on the user's input and the current state of devices.
   - *Requirement:* Handle the logic where the LLM converts "I'm going to sleep" -> `turn_off(all_lights)`.
4. Build a `main.py` with a simple CLI loop:
   - User types command.
   - Agent processes it.
   - Simulator executes it and prints the result.
   - Loop continues.
5. Create a `.env.example` file for the API Key.
6. Push the final code.

Start by defining the Tool/Function schemas based on our `SmartDevice` classes.
