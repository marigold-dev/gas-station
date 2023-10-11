INSERT INTO users("id", "name", "address", "credits")
        VALUES
        ('164b18e2-205b-47fa-8fa5-e9961b3a8437', 'Alfred', 'tz1VLKbNYhmfyQSZzsdLWrbtVbyjsRf9qEjN', '10000000'),
        ('b8c23360-9a81-4450-93d8-ea32a2d7467e', 'Quentin', 'tz1YdFws2E182i25ezpHvEvcn4vh74XcMDFi', '643535536');


INSERT INTO contracts("id", "address", "name", "owner_id")
        VALUES
        ('c8b3f63a-9453-4e9f-98b3-855a0de682aa', 'KT1Re88VMEJ7TLHTkXSHQYZQTD3MP3k7j6Ar', 'NFT weapons', '164b18e2-205b-47fa-8fa5-e9961b3a8437'),
        ('f08660dc-34a8-4575-b53c-19d362296ead', 'KT1Rp1rgfwS25XrWU6fUnR8cw6KMZBhDvXdq', 'Staking contract', '164b18e2-205b-47fa-8fa5-e9961b3a8437'),
        ('4dfbd6f2-ca41-48d0-adc5-9c0bef8127d1', 'KT1FkUTvJxzPMGNFkD8ccrjESKWAqvkzUPr4', 'Another contract', 'b8c23360-9a81-4450-93d8-ea32a2d7467e');


INSERT INTO entrypoints("id", "name", "is_enabled", "contract_id")
        VALUES
        ('1d4b9453-fbef-429d-a953-5fc14a7cf2f0', 'mint_token', true, 'c8b3f63a-9453-4e9f-98b3-855a0de682aa'),
        ('dd225743-65b8-465d-849b-be5f795b0e3e', 'permit', true, 'c8b3f63a-9453-4e9f-98b3-855a0de682aa'),
        ('18e7ee0d-6e16-4392-9cc7-1609d6f84c0c', 'stake', true, 'c8b3f63a-9453-4e9f-98b3-855a0de682aa'),
        ('33532a9c-51e7-4f88-b60f-67530122c349', 'unstake', false, 'c8b3f63a-9453-4e9f-98b3-855a0de682aa'),
        ('764d5857-1201-4a69-bbe8-137e0326a830', 'dummy', false, '4dfbd6f2-ca41-48d0-adc5-9c0bef8127d1');