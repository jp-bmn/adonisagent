import { createBrowserClient, listSignals } from '@adonis/db';
async function run() {
  const db = createBrowserClient();
  const signals = await listSignals(db, { limit: 5 });
  console.log(signals);
}
run();
