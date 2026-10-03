INSERT INTO cooks (name, phone, area, address, channel, batch_limit, completed_orders) VALUES
  ('Priya Sharma', '+911111111111', 'Koramangala', '12 1st Cross, Koramangala 4th Block, Bengaluru', 'sms', 5, 0),
  ('Rajesh Iyer',  '+912222222222', 'Indiranagar',  '88 100ft Rd, Indiranagar, Bengaluru',           'voice', 5, 0),
  ('Sunita Devi',  '+913333333333', 'Koramangala',  '7 5th Main, Koramangala 6th Block, Bengaluru', 'sms', 20, 0);

INSERT INTO listings (cook_id, dish, region, portions, price_inr, date, pickup_start, pickup_end, status) VALUES
  ((SELECT id FROM cooks WHERE phone='+911111111111'), 'Masala Dosa',       'South Indian', 8, 90,  CURRENT_DATE, '12:00', '14:00', 'open'),
  ((SELECT id FROM cooks WHERE phone='+911111111111'), 'Bisi Bele Bath',    'Karnataka',    5, 110, CURRENT_DATE, '12:30', '14:30', 'open'),
  ((SELECT id FROM cooks WHERE phone='+912222222222'), 'Chettinad Chicken', 'Tamil',        6, 180, CURRENT_DATE, '19:00', '21:00', 'open');
