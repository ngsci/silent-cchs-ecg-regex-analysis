# Wall Motion Abnormality

We are interested in wall motion abnormalities, which are abnormalities in the contractile function of the left ventricle. We also reviewed a few echocardiograms with wall motion abnormalities using a general regex*  and identified additional features of interest:
1. `NormalWM`
2. `GlobalWM`
3. `RWMA`
4. `Prior`
5. `TechnicalLimited`

*The general regex we used was `hypokin\w*|dyskin\w*|akin\w*|scarring|thinning|deteriorate|anterior|anteroseptal|inferoseptal|interior|inferolateral|anterolateral|septal|lateral|apex`.

## ekg_cardiology_echo_all_wma
The table `Nightingale.dbo.ekg_cardiology_echo_all_wma` includes the features of interest (`NormalWM`, `GlobalWM`, `RWMA`, `Prior`, `TechnicalLimited`) parsed from the echocardiogram report. 

### Step 1: Assign features at the sentence level
Table: `Nightingale.dbo.ekg_cardiology_echo_narrative_wma`

```bash
python ekg_cardiology_echo_narrative_wma.py

# ...created 28 feature columns
# ...created 6 group columns
# ...finished writing to SQL table: ekg_cardiology_echo_narrative_wma, shape: (328642, 44) (2,100.15 seconds = 35.00 minutes)
```

Dependent on:
    - `Nightingale.dbo.ekg_cardiology_echo_findings`
    - `Nightingale.dbo.ekg_cardiology_echo_conclusions`

Overview of script:
1. Retrieve "Conclusions" and "Findings - Left Ventricle" sections of the free text echocardiogram report. This will be saved in the columns `Section` and `Narrative`.
2. Split the `Narrative` report into sentences.
3. Look for features (see function `get_wm_features()` for more details) within each sentence.
    - At a high level, we have feature groups (i.e. `global_wma`) with a list of regexes (i.e. `[r'global', r'diffuse']`). 
    - Each sentence will have a flag for the regex and a flag for the feature group (`has_`).
4. Save sentence-level features in `ekg_cardiology_echo_narrative_wma`.

### Step 2: Combine all sentence-level features into a report-level feature
Table: `Nightingale.dbo.ekg_cardiology_echo_all_wma`

```bash
sqlcmd -S DWVM -i ekg_cardiology_echo_all_wma.sql
```

Output: (run on Fri 10/1)
```
N_PAT_ID    N_ECHO      MIN_ECHO_DATE    MAX_ECHO_DATE    N_NormalWM  N_GlobalWM  N_RWMA      N_Prior     N_TechnicalLimited
----------- ----------- ---------------- ---------------- ----------- ----------- ----------- ----------- ------------------
      15183       24211       2012-07-01       2021-03-01       12168        2569        2193        4531               6828
```

We create the following features:
1. `NormalWM`: A normal wall motion is when the word "normal" for wall motion must be mentioned. An example is:
    ```
    Global left ventricular wall motion and contractility are within normal limits.
    ```
    - All of the below sentence-level features must be true:
        - `s_normal = 1`: A normal finding.
            - "normal" appears in the sentence.
        - `has_lv = 1`: Left ventricle or wall motion/segment finding.
            - "left ventric{le, ular}" or "wall" appears in the sentence.
        - `g_global = 1`: A global finding.
            - "global" appears in the sentence.
2. `GlobalWM`: A global wall motion is an observed impairment of multiple segments of myocardium suggesting an underlying process that affects the entire heart. An example is:
    ```
    Mild global hypokinesis of the left ventricle is observed. 
    ```
    - All of the below sentence-level features must be true:
        - `has_lv = 1`: Left ventricle or wall motion/segment finding.
            - "left ventric{le, ular}" or "wall" appears in the sentence.
        - `has_g = 1`: A global finding.
            - "global" or "diffuse" appears in the sentence.
        - `has_m = 1`: Abnormal motion observed.
            - "hypokin", "dyskin", or "akin" appears in the sentence.
        - `s_normal = 0`: Not a normal finding.
            - "normal" does not appear in the sentence.
3. `RWMA`: Regional wall motion abnormality is an observed impairment of a segment(s) of myocardium suggesting infarction and ischemia and typically involves a blocked vessel. They may also occur in the absence of coronary artery disease (examples: myocarditis, sarcoidosis and takotsubo cardiomyopathy).
    - All of the below sentence-level features must be true:
        - `has_w = 1`: A wall segment or regional observation.
            - "basal", "mid", "apical", "anteroseptal", "anterior", "anterolateral", "inferolateral", "inferior", "inferoseptal", "septal", "anterior", "lateral", "apex", "regional" appears in sentence.
        - `has_m = 1`: Abnormal motion observed.
            - "hypokin", "dyskin", or "akin" appears in the sentence.
        - `s_normal = 0`: Not a normal finding.
            - "normal" does not appear in the sentence.
        - `has_g = 0`: Not a global finding.
            - "global" or "diffuse" does not appear in the sentence.
        - `has_p = 0`: Not a prior finding.
            - "previous", "recovered", or "prior" does not appear in the sentence.
4. `Prior`: Whether the finding is a prior finding
    - All of the below sentence-level features must be true:
        - `has_p = 1`: A prior finding.
            - "previous", "recovered", or "prior" appears in the sentence.
5. `TechnicalLimited`: Technically limited echocardiograms may not have enough information captured to make an accurate assessment.
    - This is captured by a **narrative report-level** regex:
    ```
    narrative.free_text LIKE '%technically limited%' OR 
    narrative.free_text LIKE '%technically difficult%' OR
    narrative.free_text LIKE '%limited study%' OR 
    narrative.free_text LIKE '%study quality is fair%'
    ```



## References 

[Das et al. Circulation 2006](https://doi.org/10.1161/CIRCULATIONAHA.105.595892)  
[Kim et al. PLoS Medicine 2009](https://doi.org/10.1371/journal.pmed.1000057)  
[Kwong et al. Circulation 2006](https://doi.org/10.1161/CIRCULATIONAHA.105.570648)  
[Turkbey et al. JAMA 2015](https://doi.org/10.1001/jama.2015.14849)  

