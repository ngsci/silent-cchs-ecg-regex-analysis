/*
====================================================================================================================================================================================
Author:				Katie Lin
Create date:		8/24/2021
Requested by:		Nightingale Project
Report Description:	Create WMA features from free text echocardiogram report
					("Conclusions", "Findings - Left Ventricle")
Performance: 		<10 seconds
====================================================================================================================================================================================
*/

DROP TABLE IF EXISTS Nightingale.dbo.ekg_cardiology_echo_all_wma;

SELECT [PAT_ID]
      ,[PAT_MRN_ID]
      ,[HSP_ACCOUNT_ID]
      ,sentence.[Order_Number]
      ,sentence.[Accession_Number]
      ,[Procedure_Date]
	  , CASE WHEN SUM(NormalWM) > 0 THEN 1 ELSE 0 END AS NormalWM
	  , CASE WHEN SUM(GlobalWM) > 0 THEN 1 ELSE 0 END AS GlobalWM
	  , CASE WHEN SUM(RWMA) > 0 THEN 1 ELSE 0 END AS RWMA
	  , CASE WHEN SUM([Prior]) > 0 THEN 1 ELSE 0 END AS [Prior]
	  , CASE WHEN narrative.free_text LIKE '%technically limited%' OR 
				  narrative.free_text LIKE '%technically difficult%' OR
				  narrative.free_text LIKE '%limited study%' OR 
				  narrative.free_text LIKE '%study quality is fair%' THEN 1 ELSE 0 END AS TechnicalLimited
	  , narrative.free_text
INTO Nightingale.dbo.ekg_cardiology_echo_all_wma
FROM (
-- Create sentence level aggregate features
SELECT [PAT_ID]
      ,[PAT_MRN_ID]
      ,[HSP_ACCOUNT_ID]
      ,[Order_Number]
      ,[Accession_Number]
      ,[Procedure_Date]
      ,[Sentence]
	  -- Global left ventricular wall motion and contractility are within normal limits.
	  , CASE WHEN s_normal = 1 AND has_lv = 1
	  			  AND g_global = 1 AND has_p = 0 THEN 1 ELSE 0 END AS NormalWM
	  -- Mild global hypokinesis of the left ventricle is observed. 
	  , CASE WHEN has_lv = 1 AND has_g = 1
	  			  AND has_m = 1 AND s_normal = 0
				  AND has_p = 0 THEN 1 ELSE 0 END AS GlobalWM
	  , CASE WHEN has_w = 1 AND has_m = 1
	  			  AND s_normal = 0 AND has_g = 0
				  AND has_p = 0 THEN 1 ELSE 0 END AS RWMA
	  , has_p AS [Prior]
  FROM [Nightingale].[dbo].[ekg_cardiology_echo_narrative_wma]
) AS sentence
INNER JOIN (SELECT Order_Number, free_text FROM Nightingale.dbo.ekg_cardiology_echo_narrative) AS narrative
	ON narrative.Order_Number = sentence.Order_Number
GROUP BY [PAT_ID], [PAT_MRN_ID], [HSP_ACCOUNT_ID], sentence.[Order_Number]
      , [Accession_Number], [Procedure_Date], narrative.free_text


-- Statistics
SELECT COUNT(DISTINCT PAT_ID) AS N_PAT_ID
	, COUNT(DISTINCT Accession_Number) AS N_ECHO
	, MIN(Procedure_Date) AS MIN_ECHO_DATE
	, MAX(Procedure_Date) AS MAX_ECHO_DATE
	, SUM(NormalWM) AS N_NormalWM
	, SUM(GlobalWM) AS N_GlobalWM
	, SUM(RWMA) AS N_RWMA
	, SUM([Prior]) AS N_Prior
	, SUM(TechnicalLimited) AS N_TechnicalLimited
FROM Nightingale.dbo.ekg_cardiology_echo_all_wma;