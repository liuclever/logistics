import { Card } from 'tdesign-react';

interface QuickPromptListProps {
  prompts: string[];
  onPromptClick: (prompt: string) => void;
}

export function QuickPromptList({ prompts, onPromptClick }: QuickPromptListProps) {
  return (
    <Card className="panel-card" title="快捷动作">
      <div className="prompt-list">
        {prompts.map((prompt) => (
          <button key={prompt} type="button" className="prompt-chip" onClick={() => onPromptClick(prompt)}>
            {prompt}
          </button>
        ))}
      </div>
    </Card>
  );
}
