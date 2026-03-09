import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import path from 'path';

// Load .env.production
dotenv.config({ path: path.resolve(process.cwd(), '.env.production') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error("Missing Supabase credentials in .env.production");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function fixJasmine() {
  console.log("Locating user: jasmine@inp-capital.com...");
  
  // 1. Find user by email
  const { data: users, error: findError } = await supabase
    .from('profiles')
    .select('*')
    .ilike('email', '%jasmine@inp-capital.com%');
    
  if (findError) {
    console.error("Error finding user:", findError);
    return;
  }
  
  if (!users || users.length === 0) {
    console.error("User not found!");
    return;
  }
  
  const user = users[0];
  console.log("Found user:", user);
  
  // 2. Update to Pro
  console.log("Updating to Pro (20 credits)...");
  const { data: updateData, error: updateError } = await supabase
    .from('profiles')
    .update({ 
      credits_remaining: 20,
      subscription_status: 'active' 
    })
    .eq('user_id', user.user_id)
    .select();
    
  if (updateError) {
    console.error("Update failed:", updateError);
  } else {
    console.log("Success! Updated data:", updateData[0]);
  }
}

fixJasmine();