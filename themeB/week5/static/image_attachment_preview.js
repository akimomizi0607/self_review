(() => {
    function createImagePreview(selectedFile, useGalleryLayout) {
        const previewImage = document.createElement("img");
        previewImage.alt = selectedFile.name;

        const imageFileReader = new FileReader();
        imageFileReader.addEventListener("load", () => {
            previewImage.src = imageFileReader.result;
        });
        imageFileReader.readAsDataURL(selectedFile);

        if (!useGalleryLayout) {
            previewImage.className = "new-post-image-preview";
            return previewImage;
        }

        const thumbnailFrame = document.createElement("span");
        thumbnailFrame.className = "post-image-thumbnail";
        thumbnailFrame.appendChild(previewImage);
        return thumbnailFrame;
    }

    function initializeImageAttachmentPreview(imageFileInput) {
        const previewContainer = document.getElementById(imageFileInput.dataset.imagePreviewTarget);
        const existingImageGallery = document.getElementById(imageFileInput.dataset.existingImagesTarget);
        const previewWrapper = document.getElementById(imageFileInput.dataset.previewWrapperTarget);
        const useGalleryLayout = imageFileInput.dataset.previewLayout === "gallery";

        imageFileInput.addEventListener("change", () => {
            const hasSelectedImages = imageFileInput.files.length > 0;

            // 編集時は、保存済み画像か差し替え候補のどちらかを表示する。
            if (existingImageGallery) {
                existingImageGallery.hidden = hasSelectedImages;
            }
            if (previewWrapper) {
                previewWrapper.hidden = !hasSelectedImages;
            }

            previewContainer.replaceChildren();
            for (const selectedFile of imageFileInput.files) {
                previewContainer.appendChild(createImagePreview(selectedFile, useGalleryLayout));
            }
        });
    }

    document.querySelectorAll("[data-image-preview-target]").forEach(initializeImageAttachmentPreview);
})();
