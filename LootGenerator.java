import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class LootGenerator {

    static class ItemBlueprint{
        String name;
        int minValue;
        int maxValue;
        double dropChance; // 0.0 to 1.0 (Higher = Common)

        public ItemBlueprint(String name, int min, int max, double chance){
            this.name = name;
            this.minValue = min;
            this.maxValue = max;
            this.dropChance = chance;
        }
    }
    public static void main(String[] args){

        List<ItemBlueprint> lootTable = new ArrayList<>();

        // COMMON ITEMS
        lootTable.add(new ItemBlueprint("Rusty Dagger", 1, 5, 1.0));
        lootTable.add(new ItemBlueprint("Torn Cloth", 1, 3, 1.0));
        lootTable.add(new ItemBlueprint("Wolf Pelt", 5, 10, 0.8));
        
        // UNCOMMON ITEMS
        lootTable.add(new ItemBlueprint("Iron Sword", 25, 40, 0.4));
        lootTable.add(new ItemBlueprint("Health Potion", 15, 20, 0.5));
        
        // RARE ITEMS
        lootTable.add(new ItemBlueprint("Golden Ring", 80, 120, 0.1));
        lootTable.add(new ItemBlueprint("Ancient Scroll", 150, 250, 0.05));
        
        // LEGENDARY ITEMS
        lootTable.add(new ItemBlueprint("Dragon Scale", 400, 500, 0.01));

        int recordsToGenerate = 100; // Default
        if (args.length > 0) {
            try {
                recordsToGenerate = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.out.println("Invalid number argument. Using default 100.");
            }
        }

        Random rand = new Random();

        try (FileWriter file = new FileWriter("loot_data.json")){
            System.out.println("Generating data...");

            for (int i = 0; i < recordsToGenerate; i++){
                int playerId = rand.nextInt(1000) + 1;
                String jsonRecord;
                
                // 10% chance to generate "Bad Data" for your pipeline to catch
                if (rand.nextDouble() < 0.10) {
                    jsonRecord = generateGlitch(rand, playerId);
                } else {
                    // Normal Logic
                    ItemBlueprint item = selectRandomItem(lootTable, rand);
                    // Calculate specific value for this drop (RNG Spread)
                    int actualValue = rand.nextInt(item.maxValue - item.minValue + 1) + item.minValue;
                    
                    jsonRecord = String.format("{\"playerId\": %d, \"item\": \"%s\", \"value\": %d}", 
                        playerId, item.name, actualValue);
                }

                file.write(jsonRecord + "\n");
            }
            System.out.println("Done! 'loot_data.json' updated.");

        } catch (IOException e){
            e.printStackTrace();
        }
    }
    // Helper: Pick an item based on rarity
    private static ItemBlueprint selectRandomItem(List<ItemBlueprint> table, Random rand) {
        while (true) {
            ItemBlueprint candidate = table.get(rand.nextInt(table.size()));
            // Roll to see if we keep this item
            if (rand.nextDouble() < candidate.dropChance) {
                return candidate;
            }
        }
    }

    // Helper: Create "Bad" data
    private static String generateGlitch(Random rand, int playerId) {
        int glitchType = rand.nextInt(3);
        if (glitchType == 0) {
            // Negative Value (Hacker?)
            return String.format("{\"playerId\": %d, \"item\": \"CorruptedShard\", \"value\": -999}", playerId);
        } else if (glitchType == 1) {
            // Missing Name (Bug)
            return String.format("{\"playerId\": %d, \"item\": \"\", \"value\": 50}", playerId);
        } else {
            // Value Too High (Game Breaking)
            return String.format("{\"playerId\": %d, \"item\": \"GodModeSword\", \"value\": 999999}", playerId);
        }
    }
}