"""
Skills Manager - Class-based skill loader.
Provides 2 tools: get_skills and load_skill.

Usage:
    from src.modules.remctl.config.skills import SkillsManager
    
    # Create manager instance
    skills = SkillsManager()
    
    # Register tools in your MCP server
    skills.get_tools(mcp)
"""

from pathlib import Path
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP


class SkillsManager:
    """Manages skill documentation from markdown files."""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._skills_path = Path(__file__).parent.parent / "skills"
    
    def get_skills_path(self) -> Path:
        """Get skills directory."""
        return self._skills_path
    
    def discover_skills(self) -> List[str]:
        """List all available skill names."""
        return [f.stem for f in self._skills_path.glob("*.md")]
    
    def load_skill_content(self, skill_name: str) -> str:
        """Load skill content by name."""
        if skill_name not in self._cache:
            file_path = self._skills_path / f"{skill_name}.md"
            if not file_path.exists():
                raise FileNotFoundError(f"Skill '{skill_name}' not found")
            self._cache[skill_name] = file_path.read_text(encoding='utf-8')
        return self._cache[skill_name]
    
    def get_tools(self, mcp: FastMCP):
        """
        Register skill tools to MCP server.
        
        Usage in your main server:
            from src.modules.remctl.config.skills import SkillsManager
            
            mcp = FastMCP('my-server')
            skills = SkillsManager()
            skills.get_tools(mcp)  # Registers get_skills and load_skill
        """
        
        @mcp.tool(name="get_skills")
        async def get_skills() -> dict:
            """List all available skills."""
            skills = self.discover_skills()
            return {
                "status": "success",
                "total": len(skills),
                "skills": skills
            }
        
        @mcp.tool(name="load_skill")
        async def load_skill(skill_name: str) -> dict:
            """
            Load a specific skill by name.
            
            Args:
                skill_name: Name of the skill to load
            """
            try:
                content = self.load_skill_content(skill_name)
                return {
                    "status": "success",
                    "skill": skill_name,
                    "content": content,
                    "lines": len(content.splitlines())
                }
            except FileNotFoundError as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "available_skills": self.discover_skills()
                }
        
        return 2
