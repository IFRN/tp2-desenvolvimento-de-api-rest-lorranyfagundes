from django.contrib import admin
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVotacao, Voto

admin.site.register(Eleitor)
admin.site.register(Eleicao)
admin.site.register(Candidato)
admin.site.register(AptidaoEleitor)
admin.site.register(RegistroVotacao)
admin.site.register(Voto)