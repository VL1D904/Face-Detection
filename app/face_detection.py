# Импортирт необходимых библиотек, для взаимодействия с изображениями и нейросетевой моделью.
import tensorflow as tf
import keras
import cv2
import matplotlib.pyplot as plt
import numpy as np


# Класс для локализации области лица на изображении.
class FaceDetection:
    # Инициализация объекта класса с обученной моделью нейросети 
    def __init__(self, model):
        self.model = model

    # Перевод изображения в формат тензора, для передачи нейросети. 
    def img2array(self, img, img_path=False):
        # Считывание изображения
        if img_path:
            img = tf.io.read_file(img)
            img = tf.image.decode_jpeg(img)

        # Перевод изображения в единый размер (224, 224)
        img = tf.image.resize(img, (224, 224))
        # Перевод в тип данных float
        img = tf.cast(img, dtype=tf.float32)
        # Нормализация изображения. Перевод данных из интервала [0, 255] в интервал [0, 1].
        img /= 255.
        # Добавления дополнительного измерения для сохранения формата размерности данных для нейросети (batch, width, height, channels).
        img = tf.expand_dims(img, axis=0)


        return img

    # Расчет классовой карты активации cam (classification activation map)
    def compute_cam(self, img_array, target=0):
        # Получение последнего сверточного слоя и полносвязного слоя классификации.
        last_conv_layer = self.model.get_layer(self.model.layers[-4].name)
        classifier_layer = self.model.get_layer(self.model.layers[-1].name)

        # Создание модели для расчета cam на основе выхода последнего сверточного слоя.
        cam_model = keras.models.Model(inputs=self.model.input,
                                       outputs=[last_conv_layer.output, self.model.output])
        
        # Получение активации последнего сверточного слоя и весов слоя классификации.
        conv_output, _ = cam_model.predict(img_array)
        class_weights = classifier_layer.get_weights()[0][:, target]

        # Создание cam на основе произведения активации последнего сверточного слоя и весов полносвязного слоя соответсвующих индексов.
        cam = np.zeros(shape=(conv_output.shape[1:3]), dtype=np.float32)
        for index, weight in enumerate(class_weights):
            cam += weight * conv_output[0, :, :, index]

        # Преобразование cam к размерам изображения (224, 224)
        cam = cv2.resize(cam, (224, 224))

        # Разворачивание cam, так как целевая метка 0
        cam = 1 - cam
        # Перевод отрицательных значений в 0 и нормализация cam
        cam = np.maximum(cam, 0)
        cam = cam / cam.max()
        return cam
    
    # Наложение cam на исходное изображение
    def apply_cam(self, img_path, cam):
        # Считывание исходного изображения и преобразование к размерам (224, 224)
        img = cv2.imread(img_path)
        img = cv2.resize(img, (224, 224))
        
        # Создание тепловой карты на основе cam и перевод ее в цветую карту jet
        heatmap = cv2.applyColorMap(np.uint8(cam * 255), cv2.COLORMAP_JET)

        # Наложение cam на исходное изображение
        output = img + heatmap 
        return output
    
    # Рассчет координат для ограничивающей рамки
    def get_bbox_from_cam(self, cam, threshold=.3):
        # Обработка cam с учетом порогового значения и перевод в формат изображения uint8
        cam = ((cam > threshold) * 255).astype(np.uint8)

        # Нахождение контуров на cam
        contours, _ = cv2.findContours(cam, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Нахождение координат левого верхнего угла ограничивающей рамки и ее длину и ширину, на основе контуров.
        x, y, w, h = cv2.boundingRect(contours[0])
        return (x, y, w, h)
    
    # При вызове объекта класса проводится решение задачи локализации лица на изображении
    def __call__(self, img, img_path=False):
        img_array = self.img2array(img, img_path) # Перевод изображения в тензор
        cam = self.compute_cam(img_array, 0) # Получение классовой карты активации
        bbox = self.get_bbox_from_cam(cam) # Получение координат ограничивающей рамки

        # Отрисовка ограничивающей рамки на исходном изображении
        if img_path:
            img = cv2.imread(img)

        (x, y, w, h) = bbox
        img = cv2.resize(img, (224, 224))
        img_with_rect = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 1)
        img_with_rect = cv2.cvtColor(img_with_rect, cv2.COLOR_BGR2RGB)

        return img_with_rect


if __name__ == '__main__':
    pass