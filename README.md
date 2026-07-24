# Xray Harmonization

## 1. Background


<p align="justify">
Generalization plays a critical role in the successful deployment of artificial intelligence systems in clinical practice. However, previous studies have shown that diagnostic models trained on medical images may fail to generalize across institutions. In particular, Zech et al. <a href="#ref1">[1]</a>. demonstrated that pneumonia detection models trained on chest X-ray datasets exhibited substantial performance degradation when applied to data from different hospitals and departments. The authors attributed this lack of generalization, in part, to variability in imaging acquisition conditions, including differences in X-ray scanners used across institutions.
</p>

<p align="justify">
From a physics perspective, such behavior of diagnostic models may be explained by differences in imaging acquisition parameters. In other words, the root of this issue lies in the physical principles underlying X-ray imaging systems. In particular, the interaction of X-ray photons with matter depends strongly on photon energy and material composition. As illustrated in Figure 1, the attenuation coefficient varies as a function of X-ray energy for different materials (i.e., biological tissues). Consequently, variations in acquisition parameters—such as tube voltage (kVp) or detector characteristics—can alter the resulting image appearance and intensity distribution, potentially affecting the performance and generalization of AI models.
</p>

<p align="center">
  <img src="plots/readme/attenuation_coefficient.png">
  <br>
  <em>Figure 1. Attenuation coefficient as a function of X-ray energy for different materials.</em>
</p>

<p align="justify">
As a result, the texture patterns visible in an image can vary systematically with acquisition energy <a href="#ref2">[2]</a>. This means that the same anatomical structures may produce distinct texture distributions under different scanner settings. For convolutional neural networks (CNNs) trained on images acquired at a specific energy range, exposure to images obtained with different beam energies effectively introduces unseen texture patterns <a href="#ref3">[3]</a>. Prior work has shown that standard CNN architectures trained on natural images often classify objects based on texture rather than shape <a href="#ref4">[4]</a>. Consequently, changes in acquisition conditions that alter image texture patterns may introduce distribution shifts that degrade model performance <a href="#ref5">[5]</a>.
</p>

<p align="justify">
Previous studies have shown that such scanner- and protocol-induced variability can significantly impact the robustness and fairness of diagnostic AI models  <a href="#ref5">[6]</a>. Addressing this source of heterogeneity is therefore essential for developing reliable and generalizable models across diverse imaging environments.

</p>
## 2. Aims
<p align="justify">
This project aims to investigate how image normalization and harmonization techniques affect the reliability and fairness of AI-based diagnostic models trained on heterogeneous X-ray datasets.  
The main objectives are as follows:
</p>

1. **Compare data normalization methods**  
   Evaluate and contrast multiple normalization and harmonization techniques (e.g., histogram matching, z-score normalization, quantile mapping, and physics-based corrections) applied to X-ray datasets acquired from scanners with varying technical characteristics.

2. **Assess their impact on diagnostic models**  
   Quantify how different normalization approaches influence the performance, calibration, and generalization of AI-based diagnostic models across diverse imaging sources and acquisition conditions.

3. **Develop practical guidelines**  
   Formulate recommendations for selecting optimal normalization strategies that improve diagnostic consistency, fairness, and robustness across imaging environments.



## 3. MIMIC Collection
<p align="justify">
The **MIMIC** (Medical Information Mart for Intensive Care) is a large collection of de-identified clinical datasets developed by the MIT Laboratory for Computational Physiology. The primary goal of the MIMIC project is to facilitate research in clinical decision support, epidemiology, and machine learning by providing open access to richly detailed patient data from intensive care units (ICUs). The datasets include information such as demographics, hospital admissions, laboratory measurements, clinical notes, procedures, medications, and physiological signals. All records are carefully de-identified in accordance with HIPAA regulations to protect patient privacy while enabling large-scale biomedical research.
Source: https://mimic.mit.edu/docs/gettingstarted/

<p align="justify">
One of the most recent and widely used versions is **MIMIC‑IV**, which contains detailed electronic health record (EHR) data for patients treated at Beth Israel Deaconess Medical Center. MIMIC-IV includes multiple relational tables describing hospital admissions, ICU stays, laboratory results, medication administration, procedures, diagnoses, and patient demographics. Compared with earlier releases, MIMIC-IV provides an improved schema, better modular organization of clinical and ICU data, and coverage of a more recent time period.
Clinical data descriptions: https://mimic.mit.edu/docs/iv/modules/
Dataset access: https://physionet.org/content/mimiciv/3.1/

<p align="justify">
For medical imaging research, the project also includes **MIMIC‑CXR**, a large dataset of chest radiographs linked to corresponding radiology reports and selected patient metadata. The dataset contains hundreds of thousands of chest X-ray studies collected from routine clinical practice. Images are typically stored in the original DICOM format, which preserves acquisition metadata such as imaging parameters, scanner information, projection type, and other attributes relevant for studying imaging variability.
Dataset access: https://physionet.org/content/mimic-cxr/2.1.0/

<p align="justify">
A related derivative dataset, **MIMIC‑CXR‑JPG**, provides the same chest radiographs converted to JPEG images along with structured labels extracted from radiology reports using natural language processing techniques. The JPEG version is designed to simplify the use of the dataset in computer vision workflows by reducing storage size and eliminating the need for specialized DICOM processing libraries. However, unlike the original MIMIC-CXR dataset, the JPEG version contains reduced metadata and does not preserve the full set of acquisition parameters available in the DICOM files.
Dataset access: https://physionet.org/content/mimic-cxr-jpg/2.1.0/

<p align="justify">
Together, these datasets form a complementary ecosystem: MIMIC-IV provides comprehensive clinical and hospital information, MIMIC-CXR supplies high-fidelity radiographic images with detailed acquisition metadata, and MIMIC-CXR-JPG offers a lightweight image representation suitable for large-scale machine learning experiments. This combination enables researchers to study both clinical outcomes and imaging characteristics, as well as their interactions, in large real-world patient populations.

<p align="justify">
MIMIC-IV provides detailed clinical information derived from electronic health records, including patient demographics, hospital admissions, diagnoses, procedures, and laboratory measurements. The MIMIC-CXR dataset contains chest radiographs stored in DICOM format together with associated radiology reports and imaging metadata, including acquisition parameters and scanner-related information. In contrast, the MIMIC-CXR-JPEG dataset provides the same chest radiographs converted to JPEG images and includes annotations extracted from radiology reports, organized into structured CSV files with disease labels suitable for training and evaluating diagnostic machine learning models.

In this prokject we used the following versions of the datasets:
MIMIC‑IV: 2.1
MIMIC‑CXR: 2.1
MIMIC‑CXR‑JPG: 3.1

## 3.1 NLP-Based Label Extraction
<p align="justify">
In MIMIC-CXR-JPG, CheXpert disease labels are generated automatically from the free-text radiology report associated with each imaging study, rather than being manually assigned to individual images. The CheXpert labeler is a rule-based NLP system that searches clinically relevant report sections, especially the impression section, for mentions of predefined chest X-ray observations such as atelectasis, cardiomegaly, consolidation, edema, pleural effusion, pneumonia, pneumothorax, support devices, and no finding. For each detected observation, the labeler analyzes the surrounding text to determine whether the finding is stated as present, explicitly absent, or uncertain, using rules for negation and uncertainty expressions. These mention-level decisions are then aggregated into one study-level label per observation. In the resulting MIMIC-CXR-JPG CheXpert label file, values typically indicate 

|       CSV value | Meaning                                         |
| --------------: | ----------------------------------------------- |
|           `1.0` | positive mention; finding is considered present |
|           `0.0` | negative mention; finding is considered absent  |
|          `-1.0` | uncertain mention                               |
| missing / blank | not mentioned                                   |

<p align="justify">
Because labels are derived at the study/report level, all images belonging to the same study, such as frontal and lateral views, inherit the same set of labels.

<p align="justify">
A study was considered positive for a disease only when the corresponding CheXpert label was `1.0`. Studies with no positive disease labels were treated as having no NLP-detected positive findings among the analyzed CheXpert observations. This should not be interpreted as proof that the patient had no disease, because labels are automatically extracted from radiology reports and missing labels may indicate that a finding was not mentioned rather than explicitly absent.

Thus:
| Situation                        | Meaning                                                                                                        |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Disease label = `1.0`            | Finding is mentioned as present                                                                                |
| Disease label = `0.0`            | Finding is explicitly mentioned as absent                                                                      |
| Disease label = `-1.0`           | Finding is uncertain                                                                                           |
| Disease label is blank / missing | Finding was not mentioned                                                                                      |
| `No Finding = 1.0`               | Report suggests no detected abnormal findings among the labeler’s target observations, with some special rules |
| No disease columns equal `1.0`   | No positive NLP-detected labels, but not necessarily a normal patient                                          |


Control studies were defined as studies without positive CheXpert labels for the analyzed disease categories.

## 5. Database

<p align="justify">
The clinical and annotation data in the MIMIC datasets are originally provided in the form of CSV files. Given the large volume of information and the substantial number of patients included in the dataset, directly working with CSV files becomes inefficient for querying and data analysis. Therefore, the CSV tables were converted into a relational database structure.

<p align="justify">
The schema description provided by the dataset authors follows a format typically designed for enterprise-level relational database management systems, such as PostgreSQL or Oracle, using standard SQL Data Definition Language (DDL) conventions. While this format is well-suited for production environments, it introduces unnecessary complexity and infrastructure overhead for research-oriented workflows.

<p align="justify">
Considering that this project is focused on data analysis rather than transactional processing, and does not require intensive concurrent read/write operations, the use of heavyweight database systems is not justified. Instead, a lightweight relational database approach was adopted. The database schema was adapted to be compatible with MySQL-style typing, providing a balance between structural clarity and ease of use.

<p align="justify">
For the design and visualization of the database structure, the schema was modeled using dbdiagram.io. The corresponding schema definition file is included in the repository, allowing users to recreate the database structure in any preferred relational database system if needed. In this project, MySQL is used as the primary reference implementation.

<p align="justify">
It is also important to note that the original dataset schema primarily focuses on patient information and clinical annotations. In order to support the goals of this project, additional tables were introduced to capture scanner-related metadata, including acquisition settings. This extension enables joint analysis of both medical data and technical imaging parameters, which is essential for studying the impact of acquisition variability on model performance.

For diagram designe used: https://dbdiagram.io/
The DBML code is stored in ./sql_scripts/database_diagram.dbml
The SQL code for DB creation is stored in ./sql_scripts/create_hosp_postgresql.sql
The MySQL code for DB creation is stored in ./sql_scripts/create_hosp_sqlite.sql



## 6. Code Description

To download the dataset use `python/download_data.ipynb`. It is important to note that you have to get an access to the data prior start downloading.

### 6.1 Dataset Creation

### 6.2 Aquisition Information Deriving

### 6.3 Training model for Scanner Type Classification
#### Labeling and Diagnosing

<p align="justify">
Based on radiologist feedback, several MIMIC-CXR labels have substantial clinical overlap. Cardiomegaly and enlarged cardiomediastinum can be combined because they describe essentially the same finding. Consolidation and pneumonia may also be merged for practical analysis, since pneumonia is the most common cause of consolidation and is often difficult to distinguish confidently on chest X-ray without clinical information. Lung opacity is a nonspecific finding that may represent consolidation, pneumonia, atelectasis, or pulmonary edema; therefore, it should be treated as a broad overlapping category rather than as a distinct disease. The remaining labels—fracture, lung lesion, pleural effusion, pleural other, pneumothorax, atelectasis, and edema—should generally be considered separate entities.

### 6.4 Deep Feature Extraction and Analysis


### 6.5 Harmonization

#### 6.5.1 Min/Max Harmonization

#### 6.5.2 Distribution Function Harmonization

#### 6.5.3 Harmonization in Fourier Space

#### 6.5.4 Image Size Impact on Harmonization



## 6. Contacts

If you have any questions, please contact us:

- **Saeed Aalahmari** – [aalahmari.saeed@gmail.com](mailto:aalahmari.saeed@gmail.com)  
- **Dmitrii Cherezov** – [dmitry.cherezov@gmail.com](mailto:dmitry.cherezov@gmail.com)  
- **Michael Gardner** – [mgardner@kfu.edu.sa](mailto:mgardner@kfu.edu.sa)


## References

<a id="ref1"></a>
1. Zech, J.R., Badgeley, M.A., Liu, M., Costa, A.B., Titano, J.J. and Oermann, E.K., 2018. Confounding variables can degrade generalization performance of radiological deep learning models. arXiv preprint arXiv:1807.00431.

<a id="ref2"></a>
2. Gao, Y., Shi, Y., Cao, W., Zhang, S. and Liang, Z., 2019. Energy enhanced tissue texture in spectral computed tomography for lesion classification. Visual Computing for Industry, Biomedicine, and Art, 2(1), p.16.

<a id="ref3"></a>
3. Chen, Y., Zhong, J., Wang, L., Shi, X., Lu, W., Li, J., Feng, J., Xia, Y., Chang, R., Fan, J. and Chen, L., 2022. Robustness of CT radiomics features: consistency within and between single-energy CT and dual-energy CT. European Radiology, 32(8), pp.5480-5490.

<a id="ref4"></a>
4. Moreno-Torres, J.G., Raeder, T., Alaiz-Rodríguez, R., Chawla, N.V. and Herrera, F., 2012. A unifying view on dataset shift in classification. Pattern recognition, 45(1), pp.521-530.

<a id="ref5"></a>
5. Cherezov, D., Fu, P. and Madabhushi, A., 2025. Quantitative assessment of impact of technical and population-based factors on fairness of AI models for chest X-ray scans. Computers in Biology and Medicine, 198, p.111147.

6. 

7. 

8. 

9. 


## Interesting papers

#### 1. 
Taguchi K, Iwanczyk JS (2013) Vision 20/20: single photon counting x-ray detectors in medical imaging. Med Phys 40(10):100901. https://doi.org/10.1118/1.4820371
Based on the paper, five energy channel images can be obtained with some PCD-XR systems.

Taguchi and Iwanczyk (2013) discuss multi-energy radiography, referred to as PCD-XR (Photon Counting Detector X-Ray imaging), as a parallel development to photon-counting CT. While the paper primarily focuses on CT, the authors explicitly state that most detector technologies, imaging methods, and clinical benefits discussed apply to X-ray imaging as well. PCD-XR systems use energy-discriminating detectors to count photons in multiple energy windows, preserving spectral information that is lost with conventional energy-integrating detectors. This enables improved contrast-to-noise ratio, dose reduction, quantitative imaging, and K-edge imaging capabilities.

At the time of publication, the paper notes that PCD-XR systems had already entered clinical use. The MicroDose Mammography system (Philips) is highlighted as a commercial example, utilizing an edge-on silicon strip PCD with a multi-slit scanning technique to achieve low-dose, high-quality images with minimal scatter. Additionally, bone mineral density systems such as Lunar iDXA (GE Healthcare) and Stratos DR (DMS-APELEM) equipped with PCDs from DxRay, Inc. had been on the market for several years. The authors conclude that PCD-XR represents not merely an evolution but a revolution in X-ray imaging, with potential for molecular imaging and personalized medicine applications.

#### 2.
Qasempour, Y., Mohammadi, A., Rezaei, M., Pouryazadanpanah, P., Ziaddini, F., Borbori, A., Shiri, I., Hajianfar, G., Janati, A., Ghasemirad, S. and Abdollahi, H., 2020. Radiographic texture reproducibility: The impact of different materials, their arrangement, and focal spot size. Journal of Medical Signals & Sensors, 10(4), pp.275-285.
Even when the kVp is the same, there are other parameters that impact reproducibility.

This study by Qasempour et al. (2020) investigated the reproducibility of radiographic texture features against changes in three specific parameters: focal spot size (0.6 mm vs. 1.2 mm), different phantom materials (wood, sponge, Plexiglas, rubber), and different arrangements of those materials. A detachable phantom was constructed with 1 cm thick sections of each material, and images were acquired using a digital radiography machine with consistent exposure parameters (40 kV, 4 mAs). Twenty-two texture features from histogram, GLCM, GLRLM, autoregressive, and wavelet families were extracted and analyzed using coefficient of variation (COV), intraclass correlation coefficient (ICC), and Bland-Altman methods to assess reproducibility.

Results showed that texture feature reproducibility varied considerably across conditions. Against changes in focal spot size, 59% of features were highly reproducible (COV ≤ 5%), while only 4.5% of features maintained this level of reproducibility against changes in phantom materials. Against changes in material arrangement, 50% of features were highly reproducible. ICC analysis showed most features had excellent test-retest reliability (>0.90) for repeated imaging of individual materials. Bland-Altman analysis identified only one feature (SumVarnc) as non-reproducible against focal spot changes. The authors conclude that radiomic textures are vulnerable to changes in materials, their arrangement, and focal spot size, emphasizing that careful analysis of these parameters is essential before clinical application of radiomics.




