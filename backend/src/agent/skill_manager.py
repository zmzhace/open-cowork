import os
import glob
import yaml
from typing import List, Dict

class Skill:
    def __init__(self, name: str, description: str, instructions: str):
        self.name = name
        self.description = description
        self.instructions = instructions

class SkillManager:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.skills: List[Skill] = []
        
    def load_skills(self):
        """Scans the skills directory for SKILL.md files and parses them."""
        self.skills = []
        skills_path = os.path.join(self.root_dir, "skills")
        if not os.path.exists(skills_path):
            os.makedirs(skills_path, exist_ok=True)
            return

        # Find all SKILL.md files in immediate subdirectories of skills/
        pattern = os.path.join(skills_path, "**", "SKILL.md")
        skill_files = glob.glob(pattern, recursive=True)
        
        for file_path in skill_files:
            try:
                self._parse_skill_file(file_path)
            except Exception as e:
                print(f"Failed to load skill from {file_path}: {e}")
                
    def _parse_skill_file(self, file_path: str):
        """Parses a SKILL.md file containing YAML frontmatter and Markdown body."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic frontmatter parsing: looks for --- at start and end of frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1]
                body_str = parts[2].strip()
                
                try:
                    metadata = yaml.safe_load(frontmatter_str) or {}
                    name = metadata.get("name", os.path.basename(os.path.dirname(file_path)))
                    description = metadata.get("description", "No description provided.")
                    
                    skill = Skill(name=name, description=description, instructions=body_str)
                    self.skills.append(skill)
                    print(f"Loaded skill: {name}")
                except yaml.YAMLError as ye:
                    print(f"YAML parsing error in {file_path}: {ye}")
        else:
            # If no frontmatter, fallback to using folder name
            name = os.path.basename(os.path.dirname(file_path))
            skill = Skill(name=name, description="No frontmatter found.", instructions=content.strip())
            self.skills.append(skill)
            
    def get_skills_prompt(self) -> str:
        """Generates an XML-formatted prompt string containing all loaded skills."""
        if not self.skills:
            return ""
            
        prompt = "<skills_available>\n"
        prompt += "You have access to the following custom skills which dictate specific workflows, behaviors, or domain knowledge you should utilize when relevant:\n\n"
        
        for skill in self.skills:
            prompt += f"<skill>\n"
            prompt += f"  <name>{skill.name}</name>\n"
            prompt += f"  <description>{skill.description}</description>\n"
            prompt += f"  <instructions>\n{skill.instructions}\n  </instructions>\n"
            prompt += f"</skill>\n\n"
            
        prompt += "</skills_available>\n"
        return prompt

# Global instance initialization placeholder
# Will be initialized centrally where the base dir is known
