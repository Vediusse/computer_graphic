document.addEventListener('DOMContentLoaded', () => {
    
    const imageUploader = document.getElementById('imageUploader');
    const fileNameSpan = document.getElementById('fileName');
    const defaultImgButtons = document.querySelectorAll('.default-img-button');

    const originalCanvas = document.getElementById('originalCanvas');
    const grayscaleCanvas = document.getElementById('grayscaleCanvas');
    const brightnessCanvas = document.getElementById('brightnessCanvas');
    const contrastCanvas = document.getElementById('contrastCanvas');

    const brightnessSlider = document.getElementById('brightnessSlider');
    const contrastSlider = document.getElementById('contrastSlider');

    const originalHistogramCanvas = document.getElementById('originalHistogramCanvas');
    const grayscaleHistogramCanvas = document.getElementById('grayscaleHistogramCanvas');
    const brightnessHistogramCanvas = document.getElementById('brightnessHistogramCanvas');
    const contrastHistogramCanvas = document.getElementById('contrastHistogramCanvas');

    
    const ctxOriginal = originalCanvas.getContext('2d');
    const ctxGrayscale = grayscaleCanvas.getContext('2d');
    const ctxBrightness = brightnessCanvas.getContext('2d');
    const ctxContrast = contrastCanvas.getContext('2d');

    const ctxOriginalHist = originalHistogramCanvas.getContext('2d');
    const ctxGrayscaleHist = grayscaleHistogramCanvas.getContext('2d');
    const ctxBrightnessHist = brightnessHistogramCanvas.getContext('2d');
    const ctxContrastHist = contrastHistogramCanvas.getContext('2d');

    let currentImage = new Image(); 
    
    currentImage.crossOrigin = "Anonymous";

    
    function clearCanvas(canvas, ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    
        canvas.width = 0;
        canvas.height = 0;
    }

    
    function setImageToCanvas(img, canvas, ctx) {
        clearCanvas(canvas, ctx); 

        const maxWidth = 300; 
        
        let scale = 1;
        if (img.width > maxWidth || img.height > maxWidth) {
            scale = Math.min(maxWidth / img.width, maxWidth / img.height);
        }

        const scaledWidth = img.width * scale;
        const scaledHeight = img.height * scale;

        canvas.width = scaledWidth;
        canvas.height = scaledHeight;
        ctx.drawImage(img, 0, 0, scaledWidth, scaledHeight);
    }

    // ГЛАВНАЯ ФУНКЦИЯ: Обновить все обработки и гистограммы
    function updateAllImagesAndHistograms() {
        if (!currentImage.src || !currentImage.complete || !currentImage.naturalWidth) {
            console.warn("Изображение не загружено или некорректно.");
            return;
        }

        // 1. Оригинал
        setImageToCanvas(currentImage, originalCanvas, ctxOriginal);
        const originalImageData = ctxOriginal.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
        drawRgbHistogram(originalImageData, originalHistogramCanvas, ctxOriginalHist);

        // 2. Чёрно-белое
        processGrayscale(originalImageData);

        // 3. Яркость
        processBrightness(originalImageData);

        // 4. Контраст
        processContrast(originalImageData);
    }

    
    function processGrayscale(originalImageData) {
        const imageData = new ImageData(
            new Uint8ClampedArray(originalImageData.data),
            originalImageData.width,
            originalImageData.height
        );
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
            const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
            data[i] = avg;     
            data[i + 1] = avg; 
            data[i + 2] = avg; 
        }
        grayscaleCanvas.width = originalImageData.width;
        grayscaleCanvas.height = originalImageData.height;
        ctxGrayscale.putImageData(imageData, 0, 0);
    
        drawRgbHistogram(imageData, grayscaleHistogramCanvas, ctxGrayscaleHist);
    }

    
    function processBrightness(originalImageData) {
        const brightness = parseInt(brightnessSlider.value); 
        const imageData = new ImageData(
            new Uint8ClampedArray(originalImageData.data),
            originalImageData.width,
            originalImageData.height
        );
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.max(0, Math.min(255, data[i] + brightness));
            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + brightness));
            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + brightness));
        }
        brightnessCanvas.width = originalImageData.width;
        brightnessCanvas.height = originalImageData.height;
        ctxBrightness.putImageData(imageData, 0, 0);
        drawRgbHistogram(imageData, brightnessHistogramCanvas, ctxBrightnessHist);
    }

    
    function processContrast(originalImageData) {
        const contrast = parseInt(contrastSlider.value); 
        const imageData = new ImageData(
            new Uint8ClampedArray(originalImageData.data),
            originalImageData.width,
            originalImageData.height
        );
        const data = imageData.data;

        
        const normalizedContrast = contrast * 2.55;

        const factor = (259 * (normalizedContrast + 255)) / (255 * (259 - normalizedContrast + 0.001));

        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.max(0, Math.min(255, factor * (data[i] - 128) + 128));
            data[i + 1] = Math.max(0, Math.min(255, factor * (data[i + 1] - 128) + 128));
            data[i + 2] = Math.max(0, Math.min(255, factor * (data[i + 2] - 128) + 128));
        }
        contrastCanvas.width = originalImageData.width;
        contrastCanvas.height = originalImageData.height;
        ctxContrast.putImageData(imageData, 0, 0);
        drawRgbHistogram(imageData, contrastHistogramCanvas, ctxContrastHist);
    }

    
    function drawRgbHistogram(imageData, canvas, ctx) {
        clearCanvas(canvas, ctx); 
        const data = imageData.data;

        const histR = new Array(256).fill(0);
        const histG = new Array(256).fill(0);
        const histB = new Array(256).fill(0);

        for (let i = 0; i < data.length; i += 4) {
            histR[data[i]]++;
            histG[data[i + 1]]++;
            histB[data[i + 2]]++;
        }

        const maxFrequencyR = Math.max(...histR);
        const maxFrequencyG = Math.max(...histG);
        const maxFrequencyB = Math.max(...histB);

        const maxFrequency = Math.max(maxFrequencyR, maxFrequencyG, maxFrequencyB);

        if (maxFrequency === 0) {
            canvas.width = 256;
            canvas.height = 150;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#eee';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#888';
            ctx.textAlign = 'center';
            ctx.fillText('Нет данных для гистограммы', canvas.width / 2, canvas.height / 2);
            return;
        }

        const histWidth = 256;
        const histHeight = 150;
        canvas.width = histWidth;
        canvas.height = histHeight;

        ctx.clearRect(0, 0, histWidth, histHeight);
        ctx.fillStyle = '#eee'; 
        ctx.fillRect(0, 0, histWidth, histHeight);

        
        const colors = {
            r: 'rgba(255, 0, 0, 0.7)',
            g: 'rgba(0, 128, 0, 0.7)', 
            b: 'rgba(0, 0, 255, 0.7)'
        };

        
        function drawChannel(histData, color) {
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.beginPath();
            for (let i = 0; i < histData.length; i++) {
                const barHeight = (histData[i] / maxFrequency) * histHeight;
                ctx.moveTo(i + 0.5, histHeight);
                ctx.lineTo(i + 0.5, histHeight - barHeight);
            }
            ctx.stroke();
        }

        drawChannel(histR, colors.r);
        drawChannel(histG, colors.g);
        drawChannel(histB, colors.b);


        
        ctx.fillStyle = '#555';
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText('0', 0, histHeight - 5);
        ctx.textAlign = 'right';
        ctx.fillText('255', histWidth, histHeight - 5);
    }

    
    imageUploader.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            fileNameSpan.textContent = file.name;
            const reader = new FileReader();
            reader.onload = (e) => {
                currentImage.onload = () => {
                    
                    currentImage.crossOrigin = null;
                    updateAllImagesAndHistograms();
                    resetSliders();
                };
                currentImage.src = e.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            fileNameSpan.textContent = 'Изображение не выбрано';
            
            [originalCanvas, grayscaleCanvas, brightnessCanvas, contrastCanvas].forEach(c => clearCanvas(c, c.getContext('2d')));
            [originalHistogramCanvas, grayscaleHistogramCanvas, brightnessHistogramCanvas, contrastHistogramCanvas].forEach(c => clearCanvas(c, c.getContext('2d')));
        }
    });

    
    defaultImgButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const imgSrc = event.target.dataset.src;
            if (imgSrc) {
                fileNameSpan.textContent = imgSrc.split('/').pop(); 
                currentImage.onload = () => {
                    currentImage.crossOrigin = "Anonymous";
                    updateAllImagesAndHistograms();
                    resetSliders();
                };
                currentImage.src = imgSrc;
            }
        });
    });

    
    function resetSliders() {
        brightnessSlider.value = 0;
        contrastSlider.value = 0;
        if (currentImage.src && currentImage.complete) {
            const originalImageData = ctxOriginal.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
            processBrightness(originalImageData);
            processContrast(originalImageData);
        }
    }

    
    brightnessSlider.addEventListener('input', () => {
        if (currentImage.src && currentImage.complete) {
            const originalImageData = ctxOriginal.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
            processBrightness(originalImageData);
        }
    });

    contrastSlider.addEventListener('input', () => {
        if (currentImage.src && currentImage.complete) {
            const originalImageData = ctxOriginal.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
            processContrast(originalImageData);
        }
    });

    
    currentImage.onload = () => {
        currentImage.crossOrigin = "Anonymous";
        updateAllImagesAndHistograms();
        resetSliders();
    };
    currentImage.src = 'images/default1.jpg'; 
    fileNameSpan.textContent = 'default1.jpg';
});