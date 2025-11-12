# Xray Harmonization

## 1. Background

This project is motivated by the work of Zech et al. [1], where the authors demonstrated that pneumonia diagnostic models failed to generalize across different hospitals and departments. One of the key factors contributing to this lack of generalization is the variability in X-ray scanners used across institutions and acquisition sites.

From a physical standpoint, this variability arises from differences in imaging parameters such as kVp (kilovoltage peak) [2] and mAs (milliampere-seconds) [3], which define the energy and amount of X-ray radiation, respectively. The relationship between these parameters and image contrast is well known in Radiology [4]: higher kVp/mAs values lead to lower image contrast. This effect is driven by the dependence of the X-ray attenuation coefficient [5] on photon energy—an inherently non-linear relationship even for the same tissue type.

As a result, the texture patterns visible in an image can vary systematically with acquisition energy [6]. This means that the same anatomical structures may produce distinct texture distributions under different scanner settings. For convolutional neural networks (CNNs) trained on images acquired at a specific energy range, exposure to images obtained with different beam energies effectively introduces unseen texture patterns [7]. Consequently, the model encounters feature distributions that differ from its training data, leading to degraded diagnostic performance [8].

Previous studies have shown that such scanner- and protocol-induced variability can significantly impact the robustness and fairness of diagnostic AI models [9]. Addressing this source of heterogeneity is therefore essential for developing reliable and generalizable models across diverse imaging environments.

## 2. Aims




## 3. MIMIC Collection

Source: https://mimic.mit.edu/docs/gettingstarted/

## 4. Metadata

Current project based on MIMIC-IV v3.1

## 5. SQLite

Create SQLite version of data storage so information can be processed via SQL language to increase repeatability and reproducibility of the work.


## 6. Code Description

To download the dataset use `python/download_data.ipynb`. It is important to note that you have to get an access to the data prior start downloading.

### 6.1 Dataset Creation

### 6.2 Aquisition Information Deriving

### 6.3 Training model for Scanner Type Classification


### 6.4 Deep Feature Extraction and Analysis


### 6.5 Harmonization

#### 6.5.1 Min/Max Harmonization

#### 6.5.2 Distribution Function Harmonization

#### 6.5.3 Harmonization in Fourier Space


## 6. Contacts

If you have any questions, please contact us:

- **Saeed Aalahmari** – [aalahmari.saeed@gmail.com](mailto:aalahmari.saeed@gmail.com)  
- **Dmitrii Cherezov** – [dmitry.cherezov@gmail.com](mailto:dmitry.cherezov@gmail.com)  
- **Michael Gardner** – [mgardner@kfu.edu.sa](mailto:mgardner@kfu.edu.sa)


## References

1.  Zech, J.R., Badgeley, M.A., Liu, M., Costa, A.B., Titano, J.J. and Oermann, E.K., 2018. Confounding variables can degrade generalization performance of radiological deep learning models. arXiv preprint arXiv:1807.00431.

2. 

3. 

4. 

5. 

6. 

7. 

8. 

9. 

