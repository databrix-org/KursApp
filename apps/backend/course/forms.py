from django import forms
from .models import Exercise, ExerciseMaterial, JupyterLabImage, validate_file_size
from django.conf import settings
import os
import re

# First, define the widget
class ClearableMultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return files.get(name)

    def value_omitted_from_data(self, data, files, name):
        return False

# Then, define the field
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", ClearableMultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

# Now we can use MultipleFileField in our form
class ExerciseMaterialForm(forms.ModelForm):
    files = MultipleFileField(
        required=False,
        help_text="Upload multiple material files"
    )

    class Meta:
        model = ExerciseMaterial
        fields = ['description']

    def save(self, exercise=None, commit=True):
        instance = super().save(commit=False)
        
        if exercise:
            instance.exercise = exercise
            
        if commit:
            instance.save()
            
        return instance

class SubmissionForm(forms.Form):
    files = MultipleFileField(
        required=True,
        help_text="Upload your submission files",
        validators=[validate_file_size]
    )
    descriptions = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text="Optional descriptions for the files (one per line)"
    )

    def clean_descriptions(self):
        descriptions = self.cleaned_data.get('descriptions', '').strip()
        if descriptions:
            return [desc.strip() for desc in descriptions.split('\n')]
        return []

    def clean(self):
        cleaned_data = super().clean()
        files = cleaned_data.get('files', [])
        descriptions = cleaned_data.get('descriptions', [])

        # If descriptions are provided, make sure they match the number of files
        if descriptions and len(descriptions) != len(files):
            raise forms.ValidationError(
                "Number of descriptions must match number of files"
            )

        return cleaned_data

class JupyterExerciseUploadForm(forms.Form):
    notebook = forms.FileField(
        help_text="Upload your Jupyter notebook (.ipynb file)",
        validators=[validate_file_size]
    )
    materials = MultipleFileField(
        required=False,
        help_text="Upload additional materials (Python files, datasets, etc.)"
    )
    jupyterlab_image = forms.FileField(
        required=False,
        help_text="Upload JupyterLab image (tar or tar.gz file)"
    )
    image_version = forms.CharField(
        required=False,
        help_text="Version of the JupyterLab image"
    )
    requirements = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="Additional requirements or dependencies"
    )

    def clean_notebook(self):
        notebook = self.cleaned_data.get('notebook')
        if notebook:
            print(f"Validating notebook file: {notebook.name}")
            if not notebook.name.endswith('.ipynb'):
                raise forms.ValidationError("Only Jupyter notebook files (.ipynb) are allowed.")
            if notebook.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                raise forms.ValidationError(f"File size cannot exceed {settings.FILE_UPLOAD_MAX_MEMORY_SIZE/(1024*1024)}MB")
        return notebook

    def clean_materials(self):
        materials = self.cleaned_data.get('materials', [])
        print(f"Validating {len(materials)} material files")
        if materials:
            allowed_extensions = ['.py', '.csv', '.json', '.txt', '.dat', '.npy', '.h5', '.pkl']
            for material in materials:
                print(f"Checking material file: {material.name} ({material.size} bytes)")
                ext = os.path.splitext(material.name)[1].lower()
                if ext not in allowed_extensions:
                    raise forms.ValidationError(
                        f"Invalid file type for {material.name}. Allowed types: {', '.join(allowed_extensions)}"
                    )
                if material.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                    raise forms.ValidationError(
                        f"File size cannot exceed {settings.FILE_UPLOAD_MAX_MEMORY_SIZE/(1024*1024)}MB"
                    )
                print(f"Material file {material.name} passed validation")
        return materials

    def clean_jupyterlab_image(self):
        image = self.cleaned_data.get('jupyterlab_image')
        if image:
            print(f"Validating JupyterLab image: {image.name}")
            valid_extensions = ['.tar', '.tar.gz', '.tgz']
            if not any(image.name.endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError(
                    "Invalid file format. Please upload a tar or tar.gz file."
                )
            if image.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                raise forms.ValidationError(
                    f"File size cannot exceed {settings.FILE_UPLOAD_MAX_MEMORY_SIZE/(1024*1024)}MB"
                )
            print(f"JupyterLab image {image.name} passed validation")
        return image

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('jupyterlab_image')
        version = cleaned_data.get('image_version')
        print("Running final form validation")

        if image and not version:
            raise forms.ValidationError(
                "Please provide a version number for the JupyterLab image."
            )
        elif version and not image:
            raise forms.ValidationError(
                "Please upload a JupyterLab image file."
            )

        print("Form validation completed successfully")
        return cleaned_data 