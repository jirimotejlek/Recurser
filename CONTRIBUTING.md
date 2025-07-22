# Contributing Guide using git

## Prerequisites
- Fork the repository to your GitHub account first
- Clone your fork locally: `git clone https://github.com/YOUR_USERNAME/Recurser.git`
- Add upstream remote: `git remote add upstream https://github.com/jirimotejlek/Recurser.git`

## Step 1: Sync Your Fork (Do this first!)
```bash
# Fetch the latest changes from the original repository
git fetch upstream

# Make sure you're on the main branch
git checkout main

# Merge the upstream changes
git merge upstream/main

# Push to your fork
git push origin main
```

## Step 2: Create Your Feature Branch
```bash
# Create and switch to a new branch
git checkout -b feature-branch-name
```

## Step 3: Make Your Changes
```bash
# Make your code changes, then stage them
git add .

# Commit with a descriptive message
git commit -m "Description of your changes"

# Push your branch to your fork
git push origin feature-branch-name
```

## Step 4: Create a Pull Request
1. Go to your forked repository on GitHub
2. You'll see a banner saying "Compare & pull request" - click it
3. Configure the pull request:
   - **Base repository**: The original repository
   - **Base branch**: Usually `main` or `master`
   - **Head repository**: Your fork
   - **Compare branch**: Your feature branch
4. Fill in the PR details:
   - Give it a descriptive title
   - Write a clear description of what changes you made and why
   - Reference any related issues (e.g., "Fixes #123")
5. Click "Create pull request"

## Best Practices
- **Test your changes** before pushing
- **Keep commits focused** - one commit per logical change
- **Write clear commit messages** - explain what and why
- **Follow the project's coding style**
- **Update your branch if needed**:
  ```bash
  git fetch upstream
  git rebase upstream/main
  ```

## After Creating the PR
- Wait for feedback from maintainers
- Make requested changes by pushing new commits to the same branch
- Your PR will update automatically with new pushes
- Be patient and respectful in discussions

## Common Issues
- **Merge conflicts**: If your PR has conflicts, sync with upstream and rebase
- **Failed tests**: Check the CI/CD results and fix any failing tests
- **Outdated branch**: Update your branch with the latest upstream changes