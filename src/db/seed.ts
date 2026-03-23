// Seed script — add your seed data here.
// Run with: npx tsx src/db/seed.ts

async function main() {
  console.log("Seeding database...");
  // Add seed logic here
  console.log("Seeding complete.");
}

main().catch((err) => {
  console.error("Seed failed:", err);
  process.exit(1);
});
