# Authored by Peter Garas for Ocom Software

from django.db import models


class Library(models.Model):
    description = models.TextField("Description")
    active_start_date = models.DateField("Active Start Date")
    active_end_date = models.DateField("Active End Date", blank=True, null=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField("Project Name", blank=False, max_length=254)
    active_start_date = models.DateField("Active Start Date")
    active_end_date = models.DateField("Active End Date", blank=True, null=True)
    description = models.TextField("Description", blank=True)
    client_name = models.CharField("Name of Client", blank=False, max_length=254)
    git_url = models.URLField("Git URL", blank=False)
    testing_url = models.URLField("Testing URL", blank=True)
    production_url = models.URLField("Production URL", blank=True)
    libraries = models.ManyToManyField(Library, through='ProjectLibrary', verbose_name="Project Library",
                                       blank=True)

    def __str__(self):
        return self.name


class ProjectLibrary(models.Model):
    library = models.ForeignKey(Library, verbose_name="Library")
    project = models.ForeignKey(Project, verbose_name="Project")
    version = models.CharField("Version Number", max_length=254)
