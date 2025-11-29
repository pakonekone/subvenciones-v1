#!/usr/bin/env python3
"""
Sistema de Filtros para Subvenciones BOE

Este módulo implementa un sistema avanzado de filtros para identificar
subvenciones y ayudas relevantes, incluyendo filtros por sector, cuantía,
beneficiarios y palabras clave personalizables.
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum


logger = logging.getLogger(__name__)


class FilterType(Enum):
    """Tipos de filtros disponibles"""
    INCLUDE = "include"  # Debe contener estas palabras
    EXCLUDE = "exclude"  # No debe contener estas palabras
    REGEX = "regex"      # Coincidencia por expresión regular
    AMOUNT = "amount"    # Filtro por cuantía
    SECTOR = "sector"    # Filtro por sector específico
    DEPARTMENT = "department"  # Filtro por organismo


@dataclass
class FilterRule:
    """Regla de filtro individual"""
    name: str
    filter_type: FilterType
    value: Any
    weight: float = 1.0  # Peso para scoring
    required: bool = False  # Si es obligatorio que se cumpla
    description: str = ""
    
    def __post_init__(self):
        if isinstance(self.filter_type, str):
            self.filter_type = FilterType(self.filter_type)


@dataclass
class FilterProfile:
    """Perfil completo de filtros para un tipo de empresa/sector"""
    name: str
    description: str
    rules: List[FilterRule]
    min_score: float = 0.5  # Score mínimo para considerar relevante
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class GrantFilter:
    """Motor de filtros para subvenciones del BOE"""
    
    def __init__(self, profiles_file: str = "filter_profiles.json"):
        self.profiles = {}
        self.profiles_file = profiles_file
        
        # Try to load from file, otherwise init defaults
        try:
            self.load_profiles_from_file(self.profiles_file)
            if not self.profiles:
                self._init_default_profiles()
        except Exception as e:
            logger.warning(f"Could not load profiles from {self.profiles_file}: {e}. Using defaults.")
            self._init_default_profiles()
    
    def _init_default_profiles(self):
        """Inicializa perfiles de filtros predeterminados"""
        
        # Perfil para Startups y PYMEs Tech
        startup_rules = [
            FilterRule("startup_keywords", FilterType.INCLUDE, 
                      ["startup", "pyme", "pequeña empresa", "microempresa", "emprendedor", 
                       "innovación", "i+d+i", "digitalización", "transformación digital"], 
                      weight=2.0, description="Palabras clave para startups"),
            
            FilterRule("tech_keywords", FilterType.INCLUDE,
                      ["tecnología", "software", "app", "inteligencia artificial", "ia", 
                       "blockchain", "fintech", "healthtech", "edtech", "cleantech"],
                      weight=1.5, description="Sectores tecnológicos"),
            
            FilterRule("next_generation", FilterType.INCLUDE,
                      ["next generation", "ngeu", "prtr", "plan de recuperación", "fondos europeos"],
                      weight=2.5, description="Fondos Next Generation EU"),
            
            FilterRule("exclude_large", FilterType.EXCLUDE,
                      ["gran empresa", "multinacional", "sector público", "administración"],
                      weight=1.0, description="Excluir grandes empresas"),
            
            FilterRule("min_amount", FilterType.AMOUNT,
                      {"min": 5000, "max": 500000},  # Entre 5K y 500K euros
                      weight=1.2, description="Rango de cuantía adecuado"),
        ]
        
        self.add_profile(FilterProfile(
            "startup_tech", 
            "Startups y PYMEs tecnológicas",
            startup_rules,
            min_score=0.6
        ))
        
        # Perfil para Sostenibilidad y Medio Ambiente
        green_rules = [
            FilterRule("green_keywords", FilterType.INCLUDE,
                      ["sostenibilidad", "medioambiente", "medio ambiente", "economía circular",
                       "energías renovables", "eficiencia energética", "carbono neutral",
                       "transición ecológica", "green", "bio", "eco"],
                      weight=2.0, description="Palabras sostenibilidad"),
            
            FilterRule("climate_keywords", FilterType.INCLUDE,
                      ["cambio climático", "emisiones", "descarbonización", "biodiversidad",
                       "agua", "residuos", "reciclaje", "movilidad sostenible"],
                      weight=1.8, description="Cambio climático y recursos"),
            
            FilterRule("eu_green_deal", FilterType.INCLUDE,
                      ["green deal", "pacto verde", "taxonomía verde", "fit for 55"],
                      weight=2.2, description="Green Deal Europeo"),
        ]
        
        self.add_profile(FilterProfile(
            "sostenibilidad",
            "Proyectos de sostenibilidad y medio ambiente", 
            green_rules,
            min_score=0.5
        ))
        
        # Perfil para Investigación y Desarrollo
        rd_rules = [
            FilterRule("research_keywords", FilterType.INCLUDE,
                      ["investigación", "desarrollo", "i+d", "i+d+i", "ciencia", "innovación",
                       "proyecto de investigación", "centro tecnológico", "universidad"],
                      weight=2.0, description="Investigación y desarrollo"),
            
            FilterRule("scientific_areas", FilterType.INCLUDE,
                      ["biotecnología", "nanotecnología", "materiales avanzados", "medicina",
                       "farmacéutico", "aeroespacial", "robótica", "automatización"],
                      weight=1.7, description="Áreas científicas"),
            
            FilterRule("collaboration", FilterType.INCLUDE,
                      ["consorcio", "colaboración", "transferencia tecnológica", "spin-off"],
                      weight=1.5, description="Colaboración científica"),
        ]
        
        self.add_profile(FilterProfile(
            "investigacion",
            "Investigación, desarrollo e innovación",
            rd_rules,
            min_score=0.4
        ))
        
        # Perfil para Formación y Empleo
        training_rules = [
            FilterRule("training_keywords", FilterType.INCLUDE,
                      ["formación", "capacitación", "cualificación", "recualificación",
                       "upskilling", "reskilling", "certificación", "competencias"],
                      weight=1.8, description="Formación y capacitación"),
            
            FilterRule("employment_keywords", FilterType.INCLUDE,
                      ["empleo", "inserción laboral", "orientación laboral", "autoempleo",
                       "trabajo", "contratación", "inclusión laboral"],
                      weight=1.5, description="Empleo y trabajo"),
            
            FilterRule("vulnerable_groups", FilterType.INCLUDE,
                      ["jóvenes", "mujeres", "desempleados", "parados de larga duración",
                       "personas con discapacidad", "mayores de 45", "rural"],
                      weight=1.3, description="Grupos vulnerables"),
        ]
        
        self.add_profile(FilterProfile(
            "formacion_empleo",
            "Formación, empleo e inclusión social",
            training_rules,
            min_score=0.4
        ))

        # Perfil para Organizaciones Sin Ánimo de Lucro
        nonprofit_rules = [
            FilterRule("nonprofit_required", FilterType.INCLUDE,
                      ["sin ánimo de lucro", "sin animo de lucro", "sin fines de lucro",
                       "entidad sin ánimo de lucro", "entidad sin animo de lucro",
                       "organización sin ánimo de lucro", "organizacion sin animo de lucro"],
                      weight=3.0, required=True, description="Palabras clave REQUERIDAS para nonprofit"),

            FilterRule("entity_types", FilterType.INCLUDE,
                      ["fundación", "fundacion", "asociación", "asociacion",
                       "ONG", "entidad social", "tercer sector", "cooperativa social",
                       "entidades no lucrativas"],
                      weight=2.0, description="Tipos de entidades sin ánimo de lucro"),

            FilterRule("social_activities", FilterType.INCLUDE,
                      ["actividades sociales", "acción social", "servicios sociales",
                       "voluntariado", "solidaridad", "beneficencia", "asistencia social",
                       "interés general", "utilidad pública"],
                      weight=1.5, description="Actividades de interés social"),

            FilterRule("exclude_profit", FilterType.EXCLUDE,
                      ["con ánimo de lucro", "empresa privada", "sociedad mercantil",
                       "sociedad anónima", "sociedad limitada", "S.A.", "S.L."],
                      weight=2.0, description="Excluir entidades con ánimo de lucro"),
        ]

        self.add_profile(FilterProfile(
            "nonprofit",
            "Organizaciones sin ánimo de lucro (ONGs, fundaciones, asociaciones)",
            nonprofit_rules,
            min_score=0.8  # Score alto para alta precisión
        ))

        # Perfil de prueba para PLACSP (muy permisivo)
        test_placsp_rules = [
            FilterRule("generic_terms", FilterType.INCLUDE,
                       ["contrato", "suministro", "servicio", "obra", "acuerdo marco", "licitación"],
                       weight=1.0, required=True, description="Términos genéricos de contratación"),
        ]

        self.add_profile(FilterProfile(
            "test_placsp",
            "Perfil de prueba para capturar todo de PLACSP",
            test_placsp_rules,
            min_score=0.1
        ))

    def add_profile(self, profile: FilterProfile):
        """Añade un nuevo perfil de filtros"""
        self.profiles[profile.name] = profile
        logger.info(f"➕ Perfil de filtros añadido: {profile.name}")
    
    def remove_profile(self, profile_name: str) -> bool:
        """Elimina un perfil de filtros"""
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            logger.info(f"➖ Perfil de filtros eliminado: {profile_name}")
            return True
        return False
    
    def get_profile(self, profile_name: str) -> Optional[FilterProfile]:
        """Obtiene un perfil de filtros"""
        return self.profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """Lista todos los perfiles disponibles"""
        return list(self.profiles.keys())
    
    def save_profiles_to_file(self, filename: str):
        """Guarda los perfiles a un archivo JSON"""
        profiles_data = {}
        for name, profile in self.profiles.items():
            profile_dict = asdict(profile)
            # Convertir FilterType enum a string
            for rule in profile_dict['rules']:
                rule['filter_type'] = rule['filter_type'].value
            profiles_data[name] = profile_dict
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Perfiles guardados en: {filename}")
    
    def load_profiles_from_file(self, filename: str):
        """Carga perfiles desde un archivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            for name, profile_dict in profiles_data.items():
                # Convertir string a FilterType enum
                # Convertir string a FilterType enum y crear objetos FilterRule
                rules_objects = []
                for rule in profile_dict['rules']:
                    rule['filter_type'] = FilterType(rule['filter_type'])
                    rules_objects.append(FilterRule(**rule))
                
                profile_dict['rules'] = rules_objects
                profile = FilterProfile(**profile_dict)
                self.profiles[name] = profile
            
            logger.info(f"📁 Perfiles cargados desde: {filename}")
        except Exception as e:
            logger.error(f"❌ Error cargando perfiles: {e}")
    
    def _apply_include_filter(self, text: str, keywords: List[str]) -> Tuple[bool, float, List[str]]:
        """Aplica filtro de inclusión"""
        text_lower = text.lower()
        matches = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        # Score basado en porcentaje de keywords encontradas
        score = len(matches) / len(keywords) if keywords else 0
        passed = len(matches) > 0
        
        return passed, score, matches
    
    def _apply_exclude_filter(self, text: str, keywords: List[str]) -> Tuple[bool, float, List[str]]:
        """Aplica filtro de exclusión"""
        text_lower = text.lower()
        matches = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        # Pasa si NO encuentra ninguna palabra excluida
        passed = len(matches) == 0
        score = 0.0 if matches else 1.0
        
        return passed, score, matches
    
    def _apply_regex_filter(self, text: str, pattern: str) -> Tuple[bool, float, List[str]]:
        """Aplica filtro de expresión regular"""
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            passed = len(matches) > 0
            score = min(len(matches) / 3, 1.0)  # Máximo score con 3+ coincidencias
            return passed, score, matches
        except re.error as e:
            logger.warning(f"⚠️  Regex inválida '{pattern}': {e}")
            return False, 0.0, []
    
    def _apply_amount_filter(self, extracted_info: Dict[str, Any], 
                           amount_criteria: Dict[str, float]) -> Tuple[bool, float]:
        """Aplica filtro de cuantía económica"""
        amounts = extracted_info.get('amounts', [])
        if not amounts:
            return False, 0.0
        
        min_amount = amount_criteria.get('min', 0)
        max_amount = amount_criteria.get('max', float('inf'))
        
        # Extraer números de las cuantías encontradas
        found_amounts = []
        for amount_text in amounts:
            # Buscar números en el texto
            numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', str(amount_text))
            for num_str in numbers:
                try:
                    # Convertir formato español a float
                    num = float(num_str.replace('.', '').replace(',', '.'))
                    found_amounts.append(num)
                except ValueError:
                    continue
        
        if not found_amounts:
            return False, 0.0
        
        # Verificar si alguna cantidad está en el rango
        for amount in found_amounts:
            if min_amount <= amount <= max_amount:
                # Score basado en qué tan cerca está del punto medio del rango
                mid_point = (min_amount + max_amount) / 2
                distance = abs(amount - mid_point) / (max_amount - min_amount)
                score = max(0.3, 1.0 - distance)  # Mínimo 0.3, máximo 1.0
                return True, score
        
        return False, 0.0
    
    def _apply_department_filter(self, grant_info: Dict[str, Any], 
                               departments: List[str]) -> Tuple[bool, float, List[str]]:
        """Aplica filtro por departamento/organismo"""
        grant_dept = grant_info.get('department', '').lower()
        matches = []
        
        for dept_keyword in departments:
            if dept_keyword.lower() in grant_dept:
                matches.append(dept_keyword)
        
        passed = len(matches) > 0
        score = len(matches) / len(departments) if departments else 0
        
        return passed, score, matches
    
    def evaluate_grant(self, grant_info: Dict[str, Any], 
                      profile_name: str,
                      extracted_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evalúa una subvención contra un perfil de filtros
        
        Args:
            grant_info: Información de la subvención
            profile_name: Nombre del perfil de filtros a usar
            extracted_info: Información extraída del PDF (opcional)
            
        Returns:
            Resultado de la evaluación
        """
        profile = self.profiles.get(profile_name)
        if not profile:
            raise ValueError(f"Perfil '{profile_name}' no encontrado")
        
        # Texto completo para análisis
        full_text = " ".join([
            grant_info.get('title', ''),
            grant_info.get('department', ''),
            grant_info.get('section', ''),
            grant_info.get('epigraph', '')
        ])
        
        if extracted_info:
            # Añadir información del PDF si está disponible
            for key, values in extracted_info.items():
                if isinstance(values, list):
                    full_text += " " + " ".join(str(v) for v in values)
        
        result = {
            'grant_id': grant_info.get('id'),
            'profile_used': profile_name,
            'passed': False,
            'total_score': 0.0,
            'weighted_score': 0.0,
            'min_score_required': profile.min_score,
            'rule_results': [],
            'matches_found': {},
            'evaluation_time': datetime.now().isoformat()
        }
        
        total_weight = 0
        weighted_score_sum = 0
        required_rules_passed = 0
        required_rules_total = 0
        
        # Evaluar cada regla
        for rule in profile.rules:
            rule_result = {
                'rule_name': rule.name,
                'rule_type': rule.filter_type.value,
                'passed': False,
                'score': 0.0,
                'weight': rule.weight,
                'required': rule.required,
                'matches': []
            }
            
            if rule.required:
                required_rules_total += 1
            
            # Aplicar filtro según tipo
            if rule.filter_type == FilterType.INCLUDE:
                passed, score, matches = self._apply_include_filter(full_text, rule.value)
                rule_result.update({'passed': passed, 'score': score, 'matches': matches})
                
            elif rule.filter_type == FilterType.EXCLUDE:
                passed, score, matches = self._apply_exclude_filter(full_text, rule.value)
                rule_result.update({'passed': passed, 'score': score, 'matches': matches})
                
            elif rule.filter_type == FilterType.REGEX:
                passed, score, matches = self._apply_regex_filter(full_text, rule.value)
                rule_result.update({'passed': passed, 'score': score, 'matches': matches})
                
            elif rule.filter_type == FilterType.AMOUNT and extracted_info:
                passed, score = self._apply_amount_filter(extracted_info, rule.value)
                rule_result.update({'passed': passed, 'score': score})
                
            elif rule.filter_type == FilterType.DEPARTMENT:
                passed, score, matches = self._apply_department_filter(grant_info, rule.value)
                rule_result.update({'passed': passed, 'score': score, 'matches': matches})
            
            # Acumular scores
            total_weight += rule.weight
            
            if rule_result['passed']:
                if rule.required:
                    required_rules_passed += 1
                
                weighted_score_sum += rule_result['score'] * rule.weight
                
                # Guardar matches para referencia
                if rule_result['matches']:
                    result['matches_found'][rule.name] = rule_result['matches']
            
            result['rule_results'].append(rule_result)
        
        # Calcular scores finales
        result['total_score'] = weighted_score_sum / total_weight if total_weight > 0 else 0.0
        result['weighted_score'] = result['total_score']
        
        # Verificar si pasa todos los criterios
        required_passed = (required_rules_total == 0 or 
                         required_rules_passed == required_rules_total)
        score_passed = result['total_score'] >= profile.min_score
        
        result['passed'] = required_passed and score_passed
        result['required_rules_passed'] = required_rules_passed
        result['required_rules_total'] = required_rules_total
        
        return result
    
    def evaluate_multiple_profiles(self, grant_info: Dict[str, Any],
                                 profile_names: List[str],
                                 extracted_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evalúa una subvención contra múltiples perfiles
        
        Args:
            grant_info: Información de la subvención
            profile_names: Lista de nombres de perfiles
            extracted_info: Información extraída del PDF (opcional)
            
        Returns:
            Resultados consolidados de la evaluación
        """
        results = {
            'grant_id': grant_info.get('id'),
            'profiles_evaluated': profile_names,
            'best_match': None,
            'best_score': 0.0,
            'passed_profiles': [],
            'all_results': {},
            'evaluation_time': datetime.now().isoformat()
        }
        
        for profile_name in profile_names:
            try:
                profile_result = self.evaluate_grant(grant_info, profile_name, extracted_info)
                results['all_results'][profile_name] = profile_result
                
                if profile_result['passed']:
                    results['passed_profiles'].append(profile_name)
                
                # Actualizar mejor match
                if profile_result['total_score'] > results['best_score']:
                    results['best_score'] = profile_result['total_score']
                    results['best_match'] = profile_name
                    
            except Exception as e:
                logger.error(f"❌ Error evaluando perfil {profile_name}: {e}")
                results['all_results'][profile_name] = {'error': str(e)}
        
        return results
    
    def get_filter_statistics(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera estadísticas de los resultados de filtrado
        
        Args:
            evaluation_results: Lista de resultados de evaluación
            
        Returns:
            Estadísticas de filtrado
        """
        if not evaluation_results:
            return {}
        
        stats = {
            'total_evaluated': len(evaluation_results),
            'total_passed': 0,
            'average_score': 0.0,
            'profile_performance': {},
            'top_matches': [],
            'score_distribution': {'0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0}
        }
        
        score_sum = 0
        profile_stats = {}
        
        for result in evaluation_results:
            score = result.get('total_score', 0)
            score_sum += score
            
            if result.get('passed'):
                stats['total_passed'] += 1
            
            # Distribución de scores
            if score <= 0.2:
                stats['score_distribution']['0-0.2'] += 1
            elif score <= 0.4:
                stats['score_distribution']['0.2-0.4'] += 1
            elif score <= 0.6:
                stats['score_distribution']['0.4-0.6'] += 1
            elif score <= 0.8:
                stats['score_distribution']['0.6-0.8'] += 1
            else:
                stats['score_distribution']['0.8-1.0'] += 1
            
            # Estadísticas por perfil
            profile_name = result.get('profile_used')
            if profile_name:
                if profile_name not in profile_stats:
                    profile_stats[profile_name] = {'evaluated': 0, 'passed': 0, 'score_sum': 0}
                
                profile_stats[profile_name]['evaluated'] += 1
                profile_stats[profile_name]['score_sum'] += score
                if result.get('passed'):
                    profile_stats[profile_name]['passed'] += 1
            
            # Top matches
            if score > 0.6:
                stats['top_matches'].append({
                    'grant_id': result.get('grant_id'),
                    'score': score,
                    'profile': profile_name
                })
        
        # Calcular promedios
        stats['average_score'] = round(score_sum / len(evaluation_results), 3)
        
        for profile, data in profile_stats.items():
            stats['profile_performance'][profile] = {
                'evaluated': data['evaluated'],
                'passed': data['passed'],
                'pass_rate': round(data['passed'] / data['evaluated'], 3),
                'average_score': round(data['score_sum'] / data['evaluated'], 3)
            }
        
        # Ordenar top matches por score
        stats['top_matches'] = sorted(stats['top_matches'], 
                                    key=lambda x: x['score'], reverse=True)[:10]
        
        return stats


def main():
    """Función principal para probar el sistema de filtros"""
    print("🎯 Sistema de Filtros BOE")
    print("=" * 30)
    
    # Crear motor de filtros
    filter_engine = GrantFilter()
    
    print(f"\n📋 Perfiles disponibles:")
    for profile_name in filter_engine.list_profiles():
        profile = filter_engine.get_profile(profile_name)
        print(f"  • {profile_name}: {profile.description}")
        print(f"    Reglas: {len(profile.rules)}, Score mínimo: {profile.min_score}")
    
    # Datos de prueba
    test_grants = [
        {
            'id': 'BOE-A-2024-TEST1',
            'title': 'Ayudas para la digitalización de PYMES mediante inteligencia artificial',
            'department': 'Ministerio de Industria, Comercio y Turismo',
            'section': 'III. Otras disposiciones'
        },
        {
            'id': 'BOE-A-2024-TEST2', 
            'title': 'Subvenciones para proyectos de economía circular y sostenibilidad',
            'department': 'Ministerio para la Transición Ecológica',
            'section': 'III. Otras disposiciones'
        },
        {
            'id': 'BOE-A-2024-TEST3',
            'title': 'Becas para formación en competencias digitales',
            'department': 'Ministerio de Educación y Formación Profesional',
            'section': 'III. Otras disposiciones'
        }
    ]
    
    print(f"\n🧪 Probando filtros con {len(test_grants)} subvenciones de ejemplo...")
    
    # Probar cada subvención con todos los perfiles
    all_results = []
    
    for grant in test_grants:
        print(f"\n📄 {grant['title'][:50]}...")
        
        # Evaluar con múltiples perfiles
        profiles_to_test = ['startup_tech', 'sostenibilidad', 'formacion_empleo']
        multi_result = filter_engine.evaluate_multiple_profiles(grant, profiles_to_test)
        
        all_results.append(multi_result)
        
        print(f"  🎯 Mejor match: {multi_result['best_match']} (score: {multi_result['best_score']:.2f})")
        print(f"  ✅ Perfiles que pasan: {multi_result['passed_profiles']}")
        
        # Mostrar detalles del mejor match
        if multi_result['best_match']:
            best_result = multi_result['all_results'][multi_result['best_match']]
            print(f"  📊 Reglas activadas:")
            for rule_result in best_result['rule_results']:
                if rule_result['passed']:
                    matches_str = ', '.join(rule_result.get('matches', [])[:3])
                    print(f"    ✓ {rule_result['rule_name']}: {matches_str}")
    
    # Guardar perfiles de ejemplo
    print(f"\n💾 Guardando perfiles en 'filter_profiles.json'...")
    filter_engine.save_profiles_to_file('filter_profiles.json')
    
    print(f"\n💡 Uso del sistema de filtros:")
    print(f"  - Crear perfiles personalizados para diferentes sectores")
    print(f"  - Ajustar weights y min_score según necesidades")
    print(f"  - Usar múltiples perfiles para capturar más oportunidades")
    print(f"  - Integrar con el orquestador principal para filtrado automático")


if __name__ == "__main__":
    main()