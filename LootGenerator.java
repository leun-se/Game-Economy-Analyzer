import java.io.FileWriter;
import java.io.IOException;
import java.util.Random;

public class LootGenerator {
    public static void main(String[] args){
        String[] items = {"GoldSword", "RustyDagger", "MagicRing", "EmptyBottle"};
        Random rand = new Random();

        try (FileWriter writer = new FileWriter("loot_data.json")){
            System.out.println("Generating data...");

            // Simulate 10 loot drops
            for (int i = 0; i < 10; i++){
                int playerId = rand.nextInt(1000);
                String item = items[rand.nextInt(items.length)];
                // random item value between 0-500
                int value = rand.nextInt(500);

                // Inject some "bad" data to simulate a bug or cheater
                if (i % 3 == 0){
                    value = -50; // Impossible value!
                } else if (i % 4 == 0){
                    item = "";
                }

                // Create a simple JSON string manually
                String jsonRecord = String.format(
                    "{\"playerId\": %d, \"item\": \"%s\", \"value\": %d}\n",
                    playerId, item, value
                );

                writer.write(jsonRecord);
            }
            System.out.println("Done! Check loot_data.json");
        }catch (IOException e){
            e.printStackTrace();
        }
    }
}