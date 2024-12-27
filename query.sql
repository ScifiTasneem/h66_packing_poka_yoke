WITH PartMaster AS (
    SELECT part_id, box_id, honing_type, od_machine
    FROM [PACKING_POKA_YOKE].[dbo].[H66_PACKING_PART_MASTER]
    WHERE box_id = '{box_id}'
)
SELECT 
    part_id,
    box_id,
    -- GRT Status
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
        ) OR EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
        ) THEN 'ACCEPT'
        ELSE 'REJECT'
    END AS GRT_Status,
    -- Multiguage Status
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
        ) OR EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING] 
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
        ) THEN 'ACCEPT'
        ELSE 'REJECT'
    END AS Multiguage_Status,
	-- honing type
	    -- Honing Type with Dresser ID
    CASE 
        WHEN honing_type IS NOT NULL THEN 
            CASE
                WHEN honing_type = 'Honing 1' THEN 'Honing 1_'
                WHEN honing_type = 'Honing 2' THEN 'Honing 2_'
                ELSE 'Honing Unknown_'
            END +
            (
                SELECT TOP 1 dresser_id 
                FROM [PACKING_POKA_YOKE].[dbo].[HONING_PART_MASTER] 
                WHERE HONING_PART_MASTER.part_id = PartMaster.part_id
            )
        ELSE NULL
    END AS Honing_Type_With_Dresser,
	-- junker type
    od_machine,
    -- GRT Scanning Time (Time_Stamp)
    CASE 
        WHEN EXISTS (
            SELECT Time_Stamp 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
        ) THEN (
            SELECT TOP 1 Time_Stamp
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT Time_Stamp 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
        ) THEN (
            SELECT TOP 1 Time_Stamp
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_Scanning_Time,
    -- GRT D3 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D3 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D3
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D3 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D3
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D3,
    -- GRT D5 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D5 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D5
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D5 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D5
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D5,
    -- GRT D6 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D6 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D6
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D6 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D6
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D6,
    -- GRT D7 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D7 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D7
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D7 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D7
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D7,
    -- GRT D8 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D8 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D8
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D8 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D8
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D8,
    -- GRT D9 from both tables
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_GRT] 
            WHERE [24M1570200_H66_1_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_GRT].D9 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D9
            FROM [24M1570200_H66_1_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_GRT] 
            WHERE [24M1570100_H66_2_GRT].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_GRT].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_GRT].D9 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D9
            FROM [24M1570100_H66_2_GRT]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS GRT_D9,
	-- Multigauging Scanning Time (Time_Stamp)
    CASE 
        WHEN EXISTS (
            SELECT Time_Stamp 
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
        ) THEN (
            SELECT TOP 1 Time_Stamp
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT Time_Stamp 
            FROM [24M1570100_H66_2_MULTIGAUGING] 
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
        ) THEN (
            SELECT TOP 1 Time_Stamp
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS Multigauging_Scanning_Time,
	-- GRT D1 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D1 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D1
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D1 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D1
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D1,
	-- GRT D2 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D2 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D2
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D2 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D2
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D2,
	-- GRT D5 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D5 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D5
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D5 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D5
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D5,
	-- GRT D6 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D6 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D6
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D6 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D6
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D6,
	-- GRT D8 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D8 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D8
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D8 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D8
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D8,
	-- GRT D9 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D9 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D9
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D9 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D9
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D9,
	-- GRT D10 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D10 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D10
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D10 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D10
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D10,
	-- GRT D11 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D11 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D11
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D11 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D11
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D11,
	-- GRT D12 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D12 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D12
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D12 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D12
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D12,
	-- GRT D16 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D16 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D16
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D16 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D16
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D16,
	-- GRT D17 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D17 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D17
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D17 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D17
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D17,
	-- GRT D20 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D20 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D20
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D20 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D20
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D20,
	-- GRT D21 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D21 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D21
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D21 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D21
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D21,
	-- GRT D22 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D22 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D22
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D22 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D22
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D22,
	-- GRT D23 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D23 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D23
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D23 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D23
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D23,
	-- GRT D24 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D24 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D24
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D24 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D24
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D24,
	-- GRT D25 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D25 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D25
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D25 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D25
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D25,
	-- GRT D26 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D26 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D26
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D26 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D26
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D26,
	-- GRT D27 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D27 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D27
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D27 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D27
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D27,
	-- GRT D28 from both tables of multigauge
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570200_H66_1_MULTIGAUGING] 
            WHERE [24M1570200_H66_1_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570200_H66_1_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570200_H66_1_MULTIGAUGING].D28 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D28
            FROM [24M1570200_H66_1_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        WHEN EXISTS (
            SELECT 1 
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE [24M1570100_H66_2_MULTIGAUGING].PART_NBR = PartMaster.part_id 
            AND [24M1570100_H66_2_MULTIGAUGING].RESULT_ID = 'ACCEPT'
            AND [24M1570100_H66_2_MULTIGAUGING].D28 IS NOT NULL
        ) THEN (
            SELECT TOP 1 D28
            FROM [24M1570100_H66_2_MULTIGAUGING]
            WHERE PART_NBR = PartMaster.part_id
            AND RESULT_ID = 'ACCEPT'
            ORDER BY Time_Stamp DESC
        )
        ELSE NULL
    END AS D28
FROM PartMaster;
